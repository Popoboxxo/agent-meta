---
spec-id: SPEC-artifact-mode-gating-2026-11-20
title: Artifact-Mode-Gating — Spec (Roadmap PR 3.4 / P18 / #1209, E-T7)
status: APPROVED (User, 2026-11-21, direkt freigegeben ohne Review)
approved: false
review-hinweis: "DRAFT — Freigabe nach Review erforderlich"
klasse: "M — neue Variablen-Familie + Renderer-Whitelist + Templates, Vertragswechsel gegen Kern-AC-05"
datum: 2026-11-20
issues: "#1209"
plan: docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md
roadmap: docs/plans/2026-11-15-master-roadmap.md
branch: feat/artifact-mode-gating
gate: "Status: APPROVED nach Review; E-Phasen-PR gemergt"
---

# Artifact-Mode-Gating — Spec (Roadmap PR 3.4 / P18 / #1209, E-T7)

> Status: APPROVED (User, 2026-11-21, direkt freigegeben ohne Review)
> spec-id: `SPEC-artifact-mode-gating-2026-11-20` (neu vergeben; vom Phase-E-Plan ist keine Spec-ID vorgegeben)
> Review-Hinweis: **DRAFT — Freigabe nach Review erforderlich.** Keine selbst erteilte Freigabe; Status wechselt ausschließlich durch User-Freigabe nach Review auf `APPROVED` (Roadmap §4 E-22).
> Dateiname: Auftrag `2026-11-20-artifact-mode-gating-spec.md`; Phase-E-Plan E-T7 nennt `2026-11-12-artifact-mode-template-gating-spec.md` („Datum beim Schreiben anpassen"). Rein organisatorische Abweichung, keine inhaltliche Entscheidung.
> Klasse: **M** (Roadmap §1 P18). Umsetzung erst nach APPROVED dieser Spec (Roadmap §2.2: „P18/P20 nur nach APPROVED-Spec", E-22).

Diese Spec ist die Ausgliederung des Spec-Kerns aus Task **E-T7** des APPROVED-referenzierten Phase-E-Plans und die Freigabegrundlage für den #1209-Nachfolge-PR (E-2 / Roadmap PR 3.4). Sie enthält **keinen Implementierungscode** und **keine neuen Entscheidungen**: alle Verträge, Werte, Codes und Zahlen stammen aus den referenzierten Quellen (siehe §7 Traceability). Wo eine Quelle keine Entscheidung hergibt, ist der Punkt als `OFFEN` markiert und nicht erfunden.

## 1. Problem / Ist-Soll

**Ist (Plan-Stand):** Der Artefaktort-Kern #1186 rendert `ARTIFACT_*`-Variablen und -Blöcke; laut Kern-AC-05 gilt „kein Template-Gate" (Kern-Spec Zeile 1111, Phase-E-Plan :66). Der Modus `files|inline|off` existiert im Kern-Schema/Resolver. Es gibt keine modus-abhängigen Template-Gates. `#1209` ist aus dem Phasen-PR abgespalten (Phase-E-Plan, Entscheidung 36/52), weil es den Kern-Vertrag ändert.

**Soll:** Je Artefakt-Klasse werden aus dem Kern-Modus zwei Template-Gate-Flags abgeleitet; Blöcke werden modusabhängig gerendert; fehlende Konfiguration reproduziert byte-identisch das heutige Output. Der Vertragswechsel gegen Kern-AC-05 wird dokumentiert (nur Vermerk an der APPROVED Kern-Spec, Entscheidung 34 / E-N3).

**Problem:** Ohne freigegebene Spec bleibt der #1209-Nachfolge-PR gesperrt (Phase-E-Plan :59/:333: E-T7 ist Gate; E-T8 erst nach `Status: APPROVED`). Die Roadmap führt #1209 als P18 mit Gate „Spec E-T7 zum Wellenstart (E-22); DRAFT bis dahin" (§3.4 PR 3.4).

## 2. Scope und Abgrenzung

### 2.1 Scope in

- Spec-Kern E-T7: Zielbild, Interface-Vertrag und Akzeptanzkriterien für #1209 (U1–U4, U7 belegt; U5/U6 als `OFFEN` markiert).
- Fixierung der Entscheidung 56 (Phase-E-Plan) als verbindlicher Vertrag: Gate-Flag-Form, Modus-Wert, Whitelist-Regel, Default-Verhalten, Dokumentationsort.
- Abbildung der Issue-ACs 1–5 auf Spec-Abschnitte (E-T7 Akzeptanz, Phase-E-Plan :346).
- Ausschließlich diese Markdown-Datei. **Docs-only**: kein Produktivcode, keine Templates, keine Config, kein Sync, kein Rebaseline. Verifiziert wird die Ableitung per Review und `git diff` (eine Datei).

### 2.2 Scope out / Nicht-Ziele

- E-T8, die eigentliche Umsetzung (Phase-E-Plan :348–353): `scripts/lib/variables.py`, `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`, `scripts/lib/standalone.py`, `docs/api/pal-variables.md`, bis zu 26 `agents/1-generic/*.md`, `tests/test_artifact_mode_gating.py`. Diese Spec ist deren Gate, nicht deren Implementierung.
- Der E-Phasen-PR (Block 0–3: #1187, #1198, Kern #1186, #1199, #1200) — läuft ohne #1209 (Entscheidung 36, U9 gelöst).
- Änderung der APPROVED Kern-Spec `docs/specs/2026-11-09-artifact-locations-matrix-spec.md` oder des APPROVED Kernplans: nur Vermerk im Phasen-PR (Entscheidung 34, E-N3).
- Phase F / #1201 / #1202 (Kinder-Addendum) und alle nicht-#1209-Pakete.

## 3. Interface-Vertrag (Datei:Symbol, Signatur, Fehlerpfade)

Alle Einträge dieses Abschnitts sind aus Phase-E-Plan Entscheidung 56 / E-T7 Step 1 wortgleich übernommen. Nicht belegte Punkte sind als `OFFEN` gekennzeichnet.

### 3.1 Gate-Flag-Ableitung (E U1 / U2, Entscheidung 56)

- **Zwei Flags je Klasse**, abgeleitet aus dem Kern-Variable `ARTIFACT_<CLASS>_MODE`:
  - `ARTIFACT_<CLASS>_MODE_FILES`
  - `ARTIFACT_<CLASS>_MODE_INLINE`
- **Wertetabelle (wortgleich Phase-E-Plan :335):**

| Modus (`ARTIFACT_<CLASS>_MODE`) | `..._MODE_FILES` | `..._MODE_INLINE` |
|---|---|---|
| `files` | `"true"` | `"false"` |
| `inline` | `"false"` | `"true"` |
| `off` | `"false"` | `"false"` |

- **Modus-Wert (E U2):** `files` bleibt (Kern-Konvention); der Issue-Text von #1209 (`file`, `_MODE_FILE`) wird im Umsetzungsschritt nach APPROVED angepasst. Kein eigener Spec-Entscheid.

### 3.2 Whitelist-Regel (E U3, Entscheidung 56; Abweichung 10)

- **Zielort:** `scripts/lib/variables.py::strip_inactive_conditional_blocks` (Plan :662, re-gemessen; Anker-Drift siehe §6).
- **Regel (Suffix-Match, wortgleich Plan :337):**
  `k.startswith("ARTIFACT_") and k.endswith(("_MODE_FILES", "_MODE_INLINE"))`
  Muster: `conditional_vars.update({k for k in variables if ...})` (Plan :689/:703/:704).
- **Fehlerpfad / Namenskollision:** Ein reiner Präfix-Match würde die bestehenden Projekt-Variablen `ARTIFACT_ZIP_CMD` / `ARTIFACT_TAR_CMD` miterfassen (`placeholders.py:59`). Der Suffix-Match schließt das aus; nachweisbar mit `test_zip_cmd_not_swallowed_by_whitelist`.

### 3.3 Default-Verhalten (E U4, Entscheidung 56)

- `scripts/lib/variables.py::_conditional_active` (Plan :604–614) gibt bei fehlender Variable `"true"` zurück (Default-Zeile :613).
- Konsequenz: „absent config reproduces today's output" (Issue-AC 1).
- **Fehlerpfad:** Die `_MODE_FILES`/`_MODE_INLINE`-Namen dürfen **nicht** in `_FALSE_DEFAULT_CONDITIONALS` (`variables.py:80`, re-gemessen; Plan nennt :59) aufgenommen werden — sonst würde jede Rolle bei fehlendem Wert abgeschaltet.

### 3.4 Registrierung / Konsistenz (E-T7 Step 1, Phase-E-Plan :341)

- `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` (`:12`): neue Namen registrieren, sonst `ERROR` in `check_builder_known_set` (`:375`, re-gemessen; Plan :323).
- `scripts/lib/standalone.py`: Standalone-Defaults mitführen.
- Kern-Pin erweitern: `tests/test_artifact_locations_placeholders.py::test_all_54_artifact_names_registered` (Kern T7) — neue Gate-Variablen brechen den Pin der 54 Namen (Abweichung 11).

### 3.5 Dokumentation (E U7, Entscheidung 56)

- `docs/api/pal-variables.md` (existiert): Template-Gate-Vertrag dokumentieren; muss `_MODE_FILES` und `_MODE_INLINE` nennen (Issue Punkt 4).

### 3.6 Als OFFEN markierte Vertragsanteile (keine Erfindung)

- **`OFFEN-1` (U5, Umfang):** Welche der 26 Templates (Kernplan: 10 Nicht-SE, 12 SE, 4 Reviewer) erhalten Gates; SE-Klassen mit `subdir` und Projektions-Variablen. Vom Plan ausdrücklich der Spec überlassen („Umfang (offen, U5, Spec entscheidet)"). Hier bewusst **nicht** entschieden.
- **`OFFEN-2` (U6, Vertragsänderung):** Inhalt der Anpassung von Kern-AC-05 („kein Template-Gate", Kern-Spec Zeile 1111) und der Kern-Tests, die kein `{{#if}}` erlauben (Plan T10 `test_fallback_mentions_inline_mode`, Kernplan :714). Umgang mit der APPROVED Kern-Spec ist festgelegt (nur Vermerk, Entscheidung 34 / E-N3), der **Inhalt** der Vertragsänderung ist offen. Hier bewusst **nicht** entschieden.

## 4. Datenfluss

1. **Input:** `ARTIFACT_<CLASS>_MODE` aus dem Kern (#1186, Werte `files|inline|off|abwesend`) + Konfiguration.
2. **Transformation 1 (Builder):** Ableitung der Flags `..._MODE_FILES` / `..._MODE_INLINE` je Klasse gemäß §3.1; Registrierung in `_BUILTIN_VARS`, Standalone-Defaults, Erweiterung des 54-Namen-Pins.
3. **Transformation 2 (Renderer):** `strip_inactive_conditional_blocks` wertet die Suffix-Whitelist (§3.2) aus; bei Modus `off` werden Blöcke entfernt, bei `files` beibehalten; fehlende Konfiguration → Default `true` (§3.3) → byte-identisches Output.
4. **Output:** gerenderte Agenten-Templates mit modus-gesteuerten Blöcken; keine unaufgelösten `ARTIFACT_*`-Marker im Output (Issue-AC 3).
5. **Persistenz:** Keine — diese Spec ist Docs-only. Die Umsetzung (E-T8) schreibt Templates/Code; deren Rebaseline (AC/G, klein/optional) erfolgt im #1209-Nachfolge-PR, nicht hier.

## 5. Akzeptanzkriterien (messbar)

### 5.1 Für diese Spec (E-T7 Gate, (E-T7 Akzeptanz, Phase-E-Plan :346))

- **AC-S1** — **Gegeben** dieser Entwurf, **wenn** das Review abgeschlossen ist, **dann** trägt die Spec `Status: APPROVED` durch User-Freigabe (nicht durch den Autor). Vorher bleibt `DRAFT` und E-T8 ist nicht ausführbar.
- **AC-S2** — **Gegeben** die Quellen, **wenn** die Abschnitte §3.1–§3.5 geprüft werden, **dann** entsprechen U1, U2, U3, U4 und U7 der Entscheidung 56 wortgleich (Wertetabelle, `files`, Suffix-Match, Default `true`, `docs/api/pal-variables.md`).
- **AC-S3** — **Gegeben** U5/U6, **wenn** die Spec freigegeben wird, **dann** sind beide Punkte in der Spec beantwortet; im aktuellen DRAFT sind sie als `OFFEN-1`/`OFFEN-2` markiert und nicht erfunden.
- **AC-S4** — **Gegeben** die Issue-ACs 1–5, **wenn** die Spec geprüft wird, **dann** ist jeder auf einen Abschnitt dieser Spec abgebildet (AC 1 → §3.3/§4; AC 2 → §3.1/§4; AC 3 → §3.4/§4; AC 4 → `OFFEN-1`/§3.6; AC 5 → `OFFEN-2`/§3.6, sofern der Issue-Text nach APPROVED nachgezogen wurde).

### 5.2 Abgeleitete, messbare AC für E-T8 (Umsetzung — nicht Teil dieser Spec)

Die following Tests sind aus Phase-E-Plan :352 übernommen; sie konkretisieren die Umsetzung und werden hier dokumentiert, nicht implementiert:

- **AC-I1** (Issue-AC 1): `test_absent_config_renders_byte_identical` — ohne Konfiguration byte-identisch zum heutigen Render.
- **AC-I2** (Issue-AC 2): `test_mode_off_removes_block_and_mode_files_keeps_it` — `off` entfernt den Block, `files` behält ihn.
- **AC-I3** (Issue-AC 3): `test_no_unresolved_artifact_if_marker_survives_render` — kein unaufgelöster Marker im Output.
- **AC-I4** (Issue-AC 4): `test_gated_templates_enumeration` — Liste der Rollen mit Pfad-Ausgabe; eine neue Rolle ohne Gate fällt durch.
- **AC-I5** (Abweichung 10 / U3): `test_zip_cmd_not_swallowed_by_whitelist` — `ARTIFACT_ZIP_CMD`/`ARTIFACT_TAR_CMD` nicht in der Whitelist, `..._MODE_FILES`/`..._MODE_INLINE` schon.
- **AC-I6** (U1/U2): `test_mode_flags_derived_from_mode` — je Klasse exakt die Wertetabelle aus §3.1.
- **AC-I7** (U4): `test_mode_flags_default_true_without_config` — `_conditional_active({}, "..._MODE_FILES") is True`; kein `_MODE_*`-Name in `_FALSE_DEFAULT_CONDITIONALS`.
- **AC-I8** (U7): `test_pal_variables_doc_lists_mode_flags` — `docs/api/pal-variables.md` nennt beide Flags.

Jede AC-I-n hat Entsprechung in einem Interface-Vertrag aus §3; AC-I4/I5 hängen zusätzlich an `OFFEN-1` (Umfang) und dürfen erst nach dessen Beantwortung konkretisiert werden.

## 6. Risiken / Annahmen

- **Annahme A1:** Der Phase-E-Plan ist die verbindliche Quelle; Anker wurden gegen `origin/main 9aa0e0c0` gemessen. Im Working Tree weicht `_FALSE_DEFAULT_CONDITIONALS` ab (real `:80`, Plan `:59`); `_conditional_active` (:625), `strip_inactive_conditional_blocks` (:683), `check_builder_known_set` (:375) sind vorhanden. Vor Umsetzung E-T0 Step 3 / Freshness erneut messen. Diese Spec führt **keine** Messung aus.
- **Annahme A2:** Die APPROVED Kern-Spec und der APPROVED Kernplan bleiben unverändert; der Vertragswechsel wird nur vermerkt (Entscheidung 34, E-N3). Kein Rebaseline in dieser Spec.
- **Risiko R1 (U5):** Der Umfang der 26 Templates ist offen; eine falsche Auswahl ändert das Render-Verhalten breit (AC-I4). Deshalb `OFFEN-1`, keine Annahme.
- **Risiko R2 (U6):** Kern-AC-05 und kern-seitige `{{#if}}`-Verbote sind APPROVED; eine inhaltliche Anpassung ohne Spec-Freigabe wäre ein Eingriff in freigegebene Verträge. Deshalb `OFFEN-2`, keine Annahme.
- **Risiko R3 (Kern-Pin):** Der 54-Namen-Pin bricht, wenn neue Flags nicht mitgeführt werden (Abweichung 11); in §3.4 als Fehlerpfad festgehalten.
- **Keine Code-Ausführung:** Alle Testergebnisse in §5.2 sind Plan-Erwartungen, nicht hier ausgeführt.

## 7. Traceability (ausschließlich referenzierte Quellen)

| Quelle | Stelle | Übernommen |
|---|---|---|
| Master-Roadmap | §1, P18 | #1209 Artifact-Mode-Gating, phase-e Block 4, S/T, RB AC/G, M; E-22: Spec E-T7 einzeln nach Review (DRAFT bis dahin) → Kopf, §2 |
| Master-Roadmap | §2.2 | „P18/P20 nur nach APPROVED-Spec (E-22)" → §1, AC-S1 |
| Master-Roadmap | §3.4, PR 3.4 | `feat/artifact-mode-gating`, P18 #1209, RB 1 (klein/optional), Gate „Spec E-T7 zum Wellenstart" → §2, §4 |
| Master-Roadmap | §4, E-22 | „Specs … #1209 … einzeln zum Wellenstart nach Review freigeben (bis dahin DRAFT)" → Status DRAFT, Review-Hinweis |
| Phase-E-Plan | E-T7 (:329–346) | Spec-Kern, U1–U7, Akzeptanz → §3, §5.1 |
| Phase-E-Plan | Entscheidung 56 / Abweichungen 9–11 | Flag-Form, `files`, Suffix-Match, Default true, 54-Pin, `docs/api/pal-variables.md` → §3.1–§3.5 |
| Phase-E-Plan | E-T8 (:348–353) | Vorgesehene Tests → §5.2 (dokumentiert, nicht implementiert) |
| Phase-E-Plan | PR-Schnitt E-2 (:59, :69) | Nachfolge-PR, Rebase auf gemergten E-Phasen-PR, Gate E-T7 → §2.2, §6 |

Nachgelagerter PR (nicht Teil dieser Spec): E-2 / Roadmap PR 3.4 / `feat/artifact-mode-gating` mit E-T8; Gate: `Status: APPROVED` dieser Spec + gemergter E-Phasen-PR.

## 8. Review-Hinweis

**DRAFT — Freigabe nach Review erforderlich.** Der Autor erteilt keine Freigabe. Nach Review durch `concept-reviewer`/User: `OFFEN-1` (U5) und `OFFEN-2` (U6) beantworten, Status auf `APPROVED` setzen und spec-id unverändert beibehalten. Erst dann wird E-T8 ausführbar (Phase-E-Plan :333).
