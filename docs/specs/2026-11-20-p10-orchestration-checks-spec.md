# P10 — Orchestration-Checks (PR 0.3 / E-05) — Spec

> Status: APPROVED (User, 2026-11-19, Roadmap approved — E-05; Spec nachgereicht durch Orchestrator, keine neue Entscheidung)
> spec-id: SPEC-p10-orchestration-checks
> Basis: `docs/plans/2026-11-15-master-roadmap.md:3` (Approval), `:41` (P10), `:130-134` (§2.4), `:152` (PR 0.3), `:273` (E-05), `:321/:330` (Issue-Titel); `.tmp/freshness-wave01.md:9`
> Branch: `chore/orchestration-checks` · Rebaseline laut Plan: **keiner**

## Problem / Ziel / Nicht-Ziele

**Problem.** PR 0.3 / P10 ist laut Freshness-Check PARTIAL. Erledigt ist nur O5 (`hybrid = reserved` in `config/project-config.schema.json:2584` und `:2724`). Vier Teilpunkte bleiben offen; diese Spec spezifiziert genau diese vier, ohne über den approbierten Plan hinauszugehen.

**Ziel.** (1) `orchestrator.enabled`/`strict` als DEPRECATED labeln (E-05), (2) `knowledge.schema-language` entfernen oder warnen, (3) `handoff.t-size-limit` Schema-Warnung + Doppel-Ausgabe prüfen (O9), (4) O10 Depth-Coherence-Check ergänzen.

**Nicht-Ziele.** Keine neuen Entscheidungen; keine Änderung der Laufzeit-Semantik von `enabled`/`strict` (nur Label, Keys bleiben funktionsfähig); kein Entfernen anderer Schema-Keys; keine Rebaseline, keine Golden-/Fixture-Änderungen; keine Änderung an `hybrid`-Description; keine Implementierung (Spec only).

## Interface Contracts

### IC-1 — Deprecation-Label (E-05)

| Ort | Key | Erwartete Änderung |
|---|---|---|
| `config/project-config.schema.json:2605-2609` | `orchestrator.enabled` | `description` beginnt mit `DEPRECATED — ` und nennt `orchestrator.mode` als Ersatz (`main-chat` statt `enabled: false`). `type`/`default` unverändert. |
| `config/project-config.schema.json:2610-2614` | `orchestrator.strict` | `description` beginnt mit `DEPRECATED — ` und nennt `orchestrator.mode: strict` / `advisory` als Ersatz. `type`/`default` unverändert. |

Fehlerpfad: keine neue Validierung, kein `additionalProperties`-Hit, kein Exit-Code-Wechsel; `sync.py --validate` bleibt bei 0 für Legacy-Konfigs. Minimal konservative Variante = Description-Präfix (existierendes Muster `:1154/:1162/:1833/:1865`), **nicht** das JSON-Schema-Keyword `"deprecated": true` (nur bei `se_output:3001` verwendet und für Config-Keys ohne Konsument). Variantenwahl → OQ-1.

### IC-2 — `knowledge.schema-language`

| Ort | Key | Erwartete Änderung |
|---|---|---|
| `config/project-config.schema.json:2070-2074` | `knowledge.schema-language` | Key bleibt, `description` beginnt mit `DEPRECATED — ` und erklärt: nicht mehr gelesen (inert), Sprache folgt den Projekt-Sprachregeln. `type: string`, `default: "auto"` unverändert. |

Beleg Inertheit: `docs/analysis/2026-11-15-fable-verification-of-unchecked.md:99-100` (kein Lesezugriff außer Schema). Fehlerpfad: keine neue Warnung, kein Entfernen (Entfernen würde `additionalProperties: false` triggern und `docs/ui/admin-ui.html:4546` sowie Doku-Referenzen beeinflussen). Alternative „entfernen" → OQ-2 (Plan widersprüchlich: §2.4 `:131` = P9/P5 vs. PR-0.3-Tabelle `:152`).

### IC-3 — `orchestrator.handoff.t-size-limit` (O9)

| Ort | Symbol / Key | Erwartete Änderung |
|---|---|---|
| `config/project-config.schema.json:2683-2688` | `orchestrator.handoff.t-size-limit` | Property bleibt definiert (`type: integer`, `default: 300`, `minimum: 1`); kein `additionalProperties: false`-Hit. Keine Description-Änderung nötig, sofern der Key bereits akzeptiert wird. |
| `scripts/lib/config.py:143-158` | `resolve_a2a_t_size_limit(config) -> int` | Single source (`DEFAULT_A2A_T_SIZE_LIMIT = 300`, `:140`) unverändert; Verhalten bleibt. |
| `scripts/lib/config.py:871` | `_validate_config(config, config_path) -> None` | Emission der Config-Validierungswarnungen so, dass jede Warnung pro Sync **höchstens einmal** erscheint. |

Fehlerpfad/Beleg: Verifikation `:49-51/:187` belegt `! Config validation warnings … 't-size-limit' was unexpected` doppelt (Validierung läuft zweimal). Genaue Duplikatquelle (Aufrufer vs. Emission) → OQ-3; Mindestannahme = Dedupe an der Emissionsstelle, ohne Exit-Code- oder Schema-Änderung.

### IC-4 — O10 Depth-Coherence-Check (neu)

| Ort | Symbol | Signatur / Vertrag |
|---|---|---|
| `scripts/lib/consistency/depth_coherence.py` (neu) | `check_depth_coherence` | `def check_depth_coherence(root: Path, config: dict | None = None, provider_config: dict | None = None) -> list[Finding]` — WARNING-only, fail-soft (degradiert zu `[]`), provider-agnostisch (kein Provider-Name im Code), gibt höchstens **ein** Finding pro Check-ID und Provider zurück. `Finding`/`Severity` aus `scripts/lib/consistency/report.py:22-34`. |
| `scripts/consistency-check.py:291-294` | globaler Check-Block | Registrierung via `findings.extend(check_depth_coherence(root))` im `if not specific_file:`-Zweig, neben `check_orchestrator_topology`. |

Eingabe-Keys (bestandsbasiert, keine neuen Keys): `orchestrator.delegation.max_depth` (`.meta-config/project.yaml`, Schema `:2696-2700`, 1..50, Default 10); Provider-Capability `required_depth` (`config/provider-capabilities.yaml`, z. B. `:164`); emittierte Tiefe `experimental.subagent_depth` (v2) / `subagent_depth` (v1, `scripts/lib/opencode_v2_config.py:479-517`) bzw. `[agents] max_depth` (`scripts/lib/dispatch_depth.py::write_dispatch_depth_config`, `:78-106`). Coercion-Einzelsource: `dispatch_depth.required_depth_int()` (`:30-40`). Bestehender Doctor-Seed: `config/known-issues.yaml:262-275` (`dispatch-depth-missing`, `toml-key agents.max_depth < required_depth`, ERROR) — nicht verändern, nicht duplizieren. Fehlerpfad: keine Exception, kein Abbruch; WARNINGs enden mit Exit 0. Semantik-Details (Check-IDs, Severity, Vergleichsumfang) → OQ-4.

## Datenfluss

```
project.yaml (orchestrator.{mode,enabled,strict,handoff.t-size-limit,delegation.max_depth},
              knowledge.schema-language)
   ├─ config/project-config.schema.json  ──> Schema-Validierung (WARN, nie hart: config.py:664-667)
   │                                            └─> Warnungs-Emission (IC-3: genau 1× pro Lauf)
   ├─ config.py::resolve_a2a_t_size_limit ──> {{A2A_T_SIZE_LIMIT}} (+ _TOKENS) ──> Templates
   └─ai-providers.yaml + provider-capabilities.yaml (required_depth)
        ├─ dispatch_depth.py::required_depth_int ──> [agents] max_depth / experimental.subagent_depth
        └─ consistency/depth_coherence.py (IC-4) ──> list[Finding] ──> consistency-check.py ──> Report
```

Persistenz: keine. Alle vier Änderungen sind Konfigurations-/Prüfungs-Metadaten; keine generierten Artefakte, daher RB „keiner" (Plan `:41/:152`).

## Acceptance Criteria

**AC-1 (IC-1).** Given ein sauberer Checkout, wenn `config/project-config.schema.json` geparst wird, dann beginnen `orchestrator.enabled.description` und `orchestrator.strict.description` mit `DEPRECATED — `, nennen `orchestrator.mode` als Ersatz, und `type`/`default` sind unverändert; `python scripts/sync.py --validate` mit einer Legacy-Konfig (`enabled`/`strict` ohne `mode`) exitet 0 ohne neue Warnung.

**AC-2 (IC-2).** Given die obige Schema-Datei, wenn `knowledge.schema-language` gelesen wird, dann ist der Key weiterhin definiert, trägt den Inert-/DEPRECATED-Hinweis und behält `default: "auto"`; eine Konfig mit `knowledge.schema-language: auto` erzeugt keine Validierungswarnung. (Reviewer-Alternative „entfernen" nur bei anderer Entscheidung in OQ-2.)

**AC-3 (IC-3).** Given `.meta-config/project.yaml` mit `orchestrator.handoff.t-size-limit: 250`, wenn `python scripts/sync.py --validate` läuft, dann ist der Exit-Code 0, die Meldung `Additional properties are not allowed ('t-size-limit' was unexpected)` erscheint nicht, und der Block `! Config validation warnings` erscheint höchstens einmal pro Validierungslauf (keine doppelte Zeile).

**AC-4 (IC-4).** Given eine Konfiguration mit einem aktiven Provider, dessen `required_depth = 2` ist und dessen emittierte Tiefe < 2 liegt, wenn `python scripts/consistency-check.py` ohne `--file` läuft, dann wird genau ein `Finding` mit stabiler Check-ID und `Severity.WARNING` emitiert, das Provider und die kollidierenden Keys benennt, und der Lauf endet ohne ERROR/Abbruch. (Vorangig OQ-4 zu bestätigen.)

## Offene Fragen + Risiken

- **OQ-1 (IC-1):** Description-Präfix `"DEPRECATED — "` vs. JSON-Schema-Keyword `"deprecated": true`. Minimal konservativ = Präfix (kein neues Keyword, kein Konsument nötig). Vom Reviewer zu bestätigen.
- **OQ-2 (IC-2):** Plan widersprüchlich — §2.4 `:131` verortet den toten Key in P9/P5, PR-0.3-Tabelle `:152` in 0.3. Minimal konservativ = Key behalten + inert labeln (kleiner Blast-Radius). Entfernen wäre Reviewer-Entscheidung.
- **OQ-3 (IC-3):** Doppel-Ausgabe entsteht durch zweimalige Validierung pro Sync (Verifikation `:51/:187`); exakter Duplikat-Aufrufer im Sync-Pfad ist nicht verifiziert. Minimal konservativ = Dedupe an der Emissionsstelle, ohne Schema-Änderung.
- **OQ-4 (IC-4):** Plan nennt nur den Titel „depth coherence check (max_depth / required_depth / subagent-depth)" (`:330`) und „Check in P10" (`:129`). Nicht entschieden: genaue Check-IDs, Severity, ob `orchestrator.delegation.max_depth` gegen `required_depth` geprüft wird und ob der bestehende Doctor-Seed (`dispatch-depth-missing`) als Referenz gilt. Minimal konservativ = WARNING-only, ein Finding pro Provider/ID, Reuse von `required_depth_int`.
- **Risiko:** Schema ist render-/validierungsrelevant; trotz RB „keiner" Änderungen an Descriptionstrings können Golden-Hashes berührt werden — vor Merge per `sync.py --validate` und Golden-Diff prüfen (Freshness `:9`).
- **ADR:** keine neue ADR erforderlich — diese Spec implementiert E-05 (Approval `:3/:273`), sie trifft keine neue Designentscheidung.

## Trace-Anker

spec-id: SPEC-p10-orchestration-checks

## Self-Review (Completeness Checklist)

- [x] Pflichtabschnitte vorhanden (Problem/Ziel/Nicht-Ziele · Interface Contracts · Datenfluss · Acceptance Criteria · Offene Fragen+Risiken · Trace-Anker)
- [x] Status-Marker exakt wie vorgegeben; kein `TBD`/Platzhalter
- [x] Vier Interface Contracts mit Datei:Symbol, Signatur, Fehlerpfad
- [x] Vier testbare ACs (Given/When/Then, observable Result), je 1:1 zu IC-1..IC-4
- [x] Dateistruktur mit `Files:`-Ownership (unten) vollständig zugeordnet
- [x] Keine neuen Entscheidungen — vier offene Punkte als OQ-1..OQ-4 markiert
- [x] Keine Implementierung, kein Commit, kein Subagent-Dispatch

### Files:

- `config/project-config.schema.json` — IC-1, IC-2, IC-3 (Schema-Keys/Descriptions)
- `scripts/lib/config.py` — IC-3 (Warnungs-Emission, Dedupe)
- `scripts/lib/consistency/depth_coherence.py` (neu) — IC-4 (Check-Logik)
- `scripts/consistency-check.py` — IC-4 (Registrierung im globalen Check-Block)
- `scripts/lib/dispatch_depth.py` — IC-4 (Reuse `required_depth_int`, nicht ändern)
- `tests/test_p10_orchestration_checks.py` (neu) — AC-1..AC-4
