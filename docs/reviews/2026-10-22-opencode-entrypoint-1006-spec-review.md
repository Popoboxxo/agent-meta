# Review: Opencode-Einstiegspunkt (#1006) — Spec

> Reviewte Datei: `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (Status: Entwurf, Rev. 1.0)
> Spec-ID: `SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22`
> Reviewer: concept-reviewer · Datum: 2026-10-22
> Kontext: `.tmp/opencode-v2-ctx.md` (Nutzerentscheidungen 1–5 bindend)

## Scope

Geprüft gegen echten Code und Tests auf Branch `docs/opencode-v2-1006-plans`:
`scripts/lib/isolation.py`, `scripts/lib/provider_transform.py`, `scripts/lib/context.py`,
`scripts/lib/sync_pipeline.py`, `scripts/lib/cli_commands.py`, `scripts/lib/active_set.py`,
`scripts/lib/providers.py`, `scripts/lib/consistency/{spec_plan,orchestrator_strict}.py`,
`config/{ai-providers,provider-capabilities,provider-tools}.yaml`, `tests/` (inkl. Szenarien),
eigenes `opencode.json` + `.opencode/agent-meta-state.json`, Opencode-Doku (permissions/agents/config).

## Formale Checks (Spec-Review-Modus §7.1)

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (`spec_plan.py:31-35`) | grün — alle 8 als `##` vorhanden, plus Entscheidungsregister/Risiken |
| Trace-Anker | grün — `spec-id: SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22` (Frontmatter + Sektion) |
| Approval-Marker | grün — `status: Entwurf` / `> Status: Entwurf`, konsistent zum Review-Stand |
| No-Placeholder | grün — kein `TODO`/`TBD`/`<platzhalter>`; `"<role>"` in IC-5 ist Schema-Notation (info) |

## Verifizierte Fakten (Stichprobe, alle korrekt)

- `provider_transform.py:384` Branch, `:408-411` Mode nur für v2 mit Default `'orchestrator'`, `:525` Kimi-Default, `:703-751` Mapping, `:819` Fallback `subagent`, Signatur `_transform_frontmatter_for_opencode` `:753-766` stimmt mit IC-3 überein (bis auf neues `deny_edit`).
- `isolation.py:179` `_read_state` (dict nur für `runtime-gate-deny`), `:191` `_write_state` (leer → Namespace weg, Sentinel), `:368` Entries, `:413` Merge, `:437-438` Parse-Fehler-Return, `:454-479` Familien-Merge/Rollback.
- `context.py:1644`, `:1677-1679`, `:1683`, `:1698-1701` korrekt.
- `sync_pipeline.py:1308-1312` / `cli_commands.py:283-287`: Aufruf nur bei Tier `permission`; `active_set` im Scope (`:1109`-Parameter bzw. `:221`).
- `provider-tools.yaml:56` `opencode_deny_critical: [Bash, Write, Edit]`.
- Kein Importzyklus: `isolation.py` importiert `providers`, `orchestrator_strict`, `io`, `log`; `provider_transform.py` importiert `isolation` nicht.
- Mammouth: `provider-capabilities.yaml:377` `runtime_gate: advisory` → `_sync_opencode_runtime_gate` läuft für Mammouth nie; der Guard wirkt nur transform-seitig über IC-1. Logik ist korrekt.
- Repo-Self-Sync: `opencode.json` ohne `default_agent`, mit `edit/bash["**"]="deny"`; State nur `runtime-gate-deny`, kein Sentinel (R-7 bestätigt); `.opencode/agents/orchestrator.md` = `mode: subagent`, `edit: allow`, `bash: deny`.
- Opencode-Doku: „Agent permissions are merged with the global config, and agent rules take precedence“ (opencode.ai/docs/permissions); „The default agent must be a primary agent … will fall back to "build" with a warning“ (opencode.ai/docs/config). Runtime-Evidenz v1 (Opencode 1.18.31): `default_agent` dokumentiert/akzeptiert (`docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:103`).

## Findings

### MAJOR

**MAJOR-1 · Konsistenz/Testbarkeit · AC-01 ist so nicht erfüllbar**
Opencode hat Tier `permission` (`provider-capabilities.yaml:149`), daher läuft `_sync_opencode_runtime_gate` für JEDES Opencode-Projekt, auch das nicht-strikte AC-01-Matrixprojekt. Nach IC-6 Schritt 3 schreibt es dort `default_agent` UND legt den State-Namespace `default-agent` an. `Opencode/.opencode/agent-meta-state.json` existiert heute im Manifest nicht (`tests/fixtures/ac01-baseline/hashes.json`) → `diff_against_manifest` meldet `added: Opencode/.opencode/agent-meta-state.json`. Die Aussage „ausschließlich die Hashes von 2 Artefakten ändern sich“ ist falsch. Zusätzlich: `tests/fixtures/slimming-golden/` und `compact-golden/` enthalten nur Claude-Artefakte (README: „Provider: Claude“) — die Klausel „nur Opencode-Orchestrator-Artefakte dürfen sich ändern“ ist dort leer.
*Fix:* AC-01 auf „2 geändert (`Opencode/.opencode/agents/orchestrator.md` nur `mode`, `Opencode/opencode.json` nur `default_agent`) + 1 hinzugefügt (`Opencode/.opencode/agent-meta-state.json`, nur `default-agent` + Sentinel)“ präzisieren; für die beiden Goldens „bleiben vollständig unverändert“ fordern. Ausdrücklich festhalten, dass das Matrixprojekt nicht-strikt ist, d. h. kein `edit: deny` im Orchestrator erwartet wird.

**MAJOR-2 · Vollständigkeit · Test-Impact unvollständig, Szenario 69 widerspricht der Spec**
Folgende Tests nageln das alte Verhalten fest und fehlen in AC-02/AC-10/AC-15:
1. `tests/scenarios/asserts/69-opencode-v2-surface.sh:141` — `assert "default_agent" not in doc, "v1 must not carry the v2-only key 'default_agent'"` (plus Kopfkommentar `:20-23` „v1 … byte-identical … no `default_agent`“) und Registry-Zeile `tests/scenarios/registry.md:116`. Bricht zwingend.
2. `tests/test_runtime_gate_wiring.py:182-208` (`test_strict_sync_writes_mapping_deny`, `test_single_provider_strict_writes_deny`) — `_provider_config()` ohne `primary-role` → nach IC-6 Schritt 2 kein Deny mehr → rot. Fehlt in der Spec komplett.
3. `tests/test_opencode_runtime_gate.py:352` (`test_absent_config_is_created_with_managed_block`) — exakter Vergleich `data == {"permission": …}`; mit `primary-role` kommt `default_agent` hinzu → nicht nur Fixture-, sondern Assertion-Anpassung nötig (AC-10 sagt „bleiben mit Fixture-Anpassung grün“).
4. `tests/test_transform_contracts.py:367` ist erfasst (AC-02) — ok.
*Fix:* AC-15 um eine explizite Liste „anzupassende Tests“ erweitern (1–3 mit Soll-Assertion: Szenario 69 Teil 1b prüft künftig `default_agent == "orchestrator"` auf v1 und das v1/unset-`cmp` bleibt; Wiring-Fixture bekommt `primary-role: orchestrator`; `:352` erwartet zusätzlich `default_agent`). Optional: neuer Wiring-Test „strict + permission ohne `primary-role` → kein Deny + Warning“ (deckt AC-10 auf Pipeline-Ebene, OQ-5 mit `active_set=None` ist dort bereits der Fall, `test_runtime_gate_wiring.py:135`).

**MAJOR-3 · Alternativen/Risiken · Folgen von `edit: deny` am Orchestrator unterschätzt, Alternative nicht gewogen**
Mit IC-3 hat der primäre Orchestrator unter Strict weder `edit` noch `bash` (`bash: deny` aus `opencode_deny_critical`). Er verliert damit jeden Schreibpfad. Das Template führt `Write` ausdrücklich für „checkpoints/artifacts“ (`agents/1-generic/orchestrator.md:344`, §9 Context guard & checkpointing); das eigene Repo hat `checkpointing: true`. R-2/OQ-3 nennen nur „`.tmp/`-Dateien“. Die naheliegende Alternative — ein agent-level Mapping statt Skalar, z. B. `edit: {"*": "deny", ".tmp/**": "allow", <checkpoint-pfad>: "allow"}` (Agent-Regeln haben laut Doku Vorrang, last-match-wins) — wird nicht gewogen; OQ-2 vergleicht nur `deny` vs. weglassen.
*Fix:* R-2 konkretisieren (betroffene Funktionen: Checkpoints/Artefakt-Archiv §9, Tier-B-Progress, `.tmp/`-Artefakte) und als ADR-5 die Optionen „Skalar `deny`“ vs. „scoped allow-list“ gegeneinander abwägen (Konsistenz mit „Router, nicht Worker“ vs. Funktionsverlust). Ergebnis in AC-11 festschreiben. Entscheidung 4 bleibt erfüllt, nur die Ausgestaltung wird belegt.

### MINOR

**MINOR-1 · Annahmen · OQ-1 ist per Doku bereits beantwortbar**
Opencode-Doku: „Agent permissions are merged with the global config, and agent rules take precedence“ + „last matching rule wins“. Die Default-Annahme von OQ-1 ist damit dokumentiert; IC-3 ist notwendig. Ebenso belegt: `default_agent` muss primary sein, sonst Fallback auf `build` (stützt die Kopplung `mode: primary` ↔ `default_agent`), und v1 (1.18.31) akzeptiert `default_agent` (`docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:103`).
*Fix:* OQ-1 auf „per Doku belegt (URL + Zitat)“ umstellen, die `opencode run`-Probe als optionale Bestätigung im Plan belassen; Evidenz für v1-Akzeptanz von `default_agent` in Problem/ADR-2 zitieren (räumt die Frage „bricht `default_agent` den v1-Freeze schema-seitig?“ aus).

**MINOR-2 · Konsistenz · Verhaltensänderung für ALLE Opencode-Projekte nicht als solche benannt**
Weil der Merge tier-, nicht strict-gesteuert ist, bekommen auch nicht-strikte Opencode-Projekte `default_agent: orchestrator` und einen primären Orchestrator (mit `edit: allow`). Primary-Agenten sind per `@`-Mention nicht als Subagent aufrufbar; der bisher dokumentierte Weg `@orchestrator` (`ai-providers.yaml:309` `orchestrator_hint`, derzeit allerdings in keinem Template gerendert) entfällt, Einstieg ist künftig Tab/Default. Problem/CHANGELOG sprechen nur vom Strict-Fall.
*Fix:* In „Ziel“ explizit „gilt unabhängig von `orchestrator.mode`“ ergänzen; Risiko R-8 „Default-Agent wechselt von `build` auf `orchestrator` in nicht-strikten Projekten“; CHANGELOG-Satz ergänzen; `mode: all` (primary + subagent) als verworfene Alternative zu `mode: primary` mit Begründung (Entscheidung 1) ins Register; `orchestrator_hint` korrigieren oder explizit an Plan B verweisen.

**MINOR-3 · Risiken · Lockout bei abweichendem Nutzer-`default_agent` unter Strict**
AC-07 (Nutzer setzt `"build"`) bzw. „Nutzer hat Key nachträglich gelöscht“ (IC-6 Schritt 3, `current != st["value"]`): `entry` ist gesetzt → Gate-Deny wird trotzdem geschrieben → der Main Chat landet im gesperrten `build` — genau das Symptom aus #1006. Gemäß Entscheidung 2 korrekt (Bedingung ist nur `primary-role` + generiert), aber unbenannt.
*Fix:* Warnungstext in AC-07 muss die Konsequenz nennen („Gate aktiv, `<user-agent>` ist gesperrt; `default_agent` auf `orchestrator` setzen oder Strict für Opencode via `provider-overrides` deaktivieren“); als Risiko R-9 aufnehmen.

**MINOR-4 · Machbarkeit · Doppelter Lazy-Import vermeidbar**
IC-3 importiert `lib.isolation` lazy in `provider_transform`, IC-4 importiert `provider_transform._explicit_primary_role` lazy in `isolation`. Beide Module importieren bereits `providers`.
*Fix:* `_explicit_primary_role` (öffentlich, z. B. `explicit_primary_role`) in `scripts/lib/providers.py` ablegen; `opencode_runtime_gate_wanted` kann in `isolation.py` bleiben (ein Lazy-Import) oder ebenfalls nach `providers.py`/`runtime_gate.py` wandern. Keine Kreuz-Lazy-Imports.

**MINOR-5 · Konsistenz · v2-Create-Pfad + Merge: `default_agent` wird nie zurückgerollt**
Auf v2 schreibt der Create-Pfad `default_agent`; der erste Merge sieht `current == desired` ohne State → `prior = desired`. Entfällt später `primary-role`, „restauriert“ der Rollback auf denselben Wert — der von agent-meta erzeugte Key bleibt dauerhaft. Für v1 neu erzeugte Dateien tritt das nicht auf (Template ohne `default_agent`).
*Fix:* In ADR-3 als bewusste Grenze dokumentieren (akzeptabel) oder AC-08 um diesen v2-Fall ergänzen.

**MINOR-6 · Konsistenz · Kommando-Pfad in AC-15**
AC-15 nennt `python3 sync.py --validate`; korrekt ist `python3 scripts/sync.py --validate` (wie AC-12e).
*Fix:* Pfad angleichen.

### INFO

- **INFO-1** Wiederholte Warnung bei jedem Sync in den „Nutzer weicht ab“-Zweigen (AC-07, IC-6 `current != st["value"]`) — akzeptabel; ggf. Plan-Hinweis, die Warnung stabil formuliert zu halten (Log-Diffing).
- **INFO-2** Bedrohungsmodell (internes Tool, vereinfacht): Hauptszenarien „Gate-Bypass über Agent-Level-Allow“ (R-1, durch IC-3 adressiert, per Doku bestätigt) und „Main-Chat-Lockout“ (Problem, R-1, MINOR-3) sind abgedeckt. Der Guard bleibt Convention boundary — Hinweis auf `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary` wäre konsistent.
- **INFO-3** OQ-4 (Rollback-Lücke bei Tier-Wechsel/Provider-Entfernung) sauber als Nicht-Ziel abgegrenzt; da Opencode-Tier statisch `permission` ist, betrifft die Lücke praktisch nur Provider-Entfernung. Folge-Issue reicht.
- **INFO-4** Mammouth-Guard-Logik korrekt: transform-seitig über IC-1 (kein Code-Default), merge-seitig nie erreicht (Tier `advisory`). AC-03 deckt es ab; ein Satz in IC-8, dass der Merge für Mammouth strukturell nicht läuft, würde die Argumentation schließen.

## Verdict

**CHANGES_REQUESTED**

Begründung: Struktur, Trace-Anker, Approval-Marker und Entscheidungstreue (1–5) sind in Ordnung; die Code-Referenzen stimmen. Drei MAJOR-Findings blockieren die Freigabe: AC-01 ist in der vorliegenden Form nicht erfüllbar (zusätzliche State-Datei im Matrixprojekt), der Test-Impact ist unvollständig (Szenario 69 :141 und `test_runtime_gate_wiring.py` brechen, ohne in der Spec vorzukommen), und die Folgen von `edit: deny` (Verlust jedes Schreibpfads inkl. Checkpoints) sind weder vollständig benannt noch gegen die scoped-allow-Alternative abgewogen. Nach Korrektur reicht ein fokussierter Re-Review der MAJOR-Punkte.
