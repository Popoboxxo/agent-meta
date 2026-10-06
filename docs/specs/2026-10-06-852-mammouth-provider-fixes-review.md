---
review-of: SPEC-852-MAMMOUTH-PROVIDER-FIXES-2026-10-06
reviewer: concept-reviewer
date: 2026-10-06
verdict: APPROVED
---

# Concept-Review — Mammouth Provider Fixes (#852/#853/#857)

## Scope

Unabhängiges Spec-Review der Mini-Spec `docs/specs/2026-10-06-852-mammouth-provider-fixes.md`
(Trace-Anker `SPEC-852-MAMMOUTH-PROVIDER-FIXES-2026-10-06`). Jede der drei gepinnten
Entscheidungen wurde gegen den realen, zitierten Code verifiziert (keine Übernahme auf
Vertrauen); die Vorher/Nachher-YAML-Snippets wurden gegen den aktuellen Dateistand
geprüft; OQ-1 wurde eigenständig gegen in-Repo-Evidenz zu lösen versucht.

## Verifikation der 3 gepinnten Entscheidungen

**#852 `model-format: "mammouth/{model}"`** — KORREKT.
- `scripts/lib/roles.py::apply_model_format` (Z. 326–346) liest `model-format` rein
  generisch aus der Config und ist idempotent (Z. 344–345: bei vorhandenem Präfix
  unverändert zurück). Kein Provider-Namen-Branch.
- Parität bestätigt: KimiCode nutzt `model-format: "kimi-code/{model}"`
  (`config/ai-providers.yaml:714`), exakt derselbe Mechanismus.
- Aktueller Wert `"{model}"` an `config/ai-providers.yaml:490` — Snippet stimmt.
- AC-2 (kein Doppelpräfix bei vorformatiertem Override): idempotenter Pfad greift,
  `mammouth/claude-sonnet-4-6` ist kein Tier → direkt in `apply_model_format` →
  `startswith("mammouth/")` → unverändert. Verifiziert.

**#853 `settings_file: mammouth.json` + `settings_template`** — KORREKT.
- `scripts/lib/context.py::_init_provider_settings_json` (Z. 1365–1408) liest
  `settings_file`/`settings_template` generisch, überspringt existierende Dateien
  (Z. 1379–1382: `"already exists — not overwritten"` → deckt AC-4 wörtlich).
- Aktueller Wert `.mammouth/settings.json` an `config/ai-providers.yaml:512` — Snippet
  stimmt.
- Byte-for-byte-Claim (§3.2) bestätigt mit Einschränkung: `apply_settings_surface_shape`
  (`context.py:1333`) gibt `content` unverändert zurück, sobald
  `mcp-config.format != "opencode-json-v2"`. Mammouth erhält `opencode-json` (nicht v2),
  also bleibt die JSONC-Datei byte-identisch. Outcome wie behauptet — siehe Finding
  MINOR-1 zur Begründungsungenauigkeit.

**#857 `mcp-config {committed-file: mammouth.json, format: opencode-json}`** — KORREKT.
- `scripts/lib/artifact_validate.py::validate_mcp_document` (Z. 328 ff.) dispatcht rein
  auf `format`; `opencode-json` ∈ `_MCP_JSON_FORMATS` (Z. 323). Fail-soft bei leerer
  Config. Kein Provider-Branch.
- `scripts/lib/mcp_provider_config.py::_update_json_config` (Z. 257–282) macht
  Read-Modify-Write unter `mcp_key` und erhält alle übrigen Top-Level-Keys (Z. 277–280)
  → #853-Settings und #857-MCP koexistieren in einer Datei wie behauptet (R-4).
- Aktueller Wert `mcp-config: {}` an `config/ai-providers.yaml:531` ist tatsächlich der
  einzige leere Eintrag — Problembeschreibung bestätigt.

**Weitere Snippet-/Zeilenprüfungen (alle exakt):**
- Mammouth-Block `config/ai-providers.yaml` Z. 483 (`Mammouth:`) bis 563 — stimmt.
- `config/provider-capabilities.yaml:250` „MCP-Integration … nicht konfiguriert" —
  wörtlich wie im Vorher-Snippet; wird durch #857 faktisch falsch, Update korrekt.
- `tests/test_provider_hooks_config.py:31` pinnt `.mammouth/settings.json` — stimmt;
  die beiden `!=`-Claude-Kollisionsasserts (Z. 32–33) halten weiter.
- `tests/test_model_contracts.py` Z. 76–80 / 133–137 / 204–208 vergleichen aktuell den
  UNFORMATIERTEN Registry-Wert (`resolved == registry_tier`). Mit dem neuen
  `model-format` lieferte der Resolver `mammouth/<tier>` → diese Asserts BRECHEN ohne
  Anpassung. Die Spec identifiziert das korrekt und stellt auf `f"mammouth/{...}"` um.
- `test_kimicode_emits_single_prefix` (Z. 211) existiert; der neue
  `test_mammouth_emits_single_prefix` spiegelt ihn und lässt korrekt den
  `model-catalog`-Check weg (Mammouth hat keinen Katalog → konsistent mit Nicht-Ziel).

## OQ-1 — eigenständige Auflösung

**OQ-1 ist bereits in-Repo auflösbar — nicht offen.** Die Spec stuft den Dateinamen
`mammouth.json` als „nicht 100% runtime-verifiziert" ein; tatsächlich liegt
Quellcode-Analyse-Evidenz im Repo vor:

- `docs/analysis/2026-09-30-provider-audit-docs-part2.md:341–342`: „Fork
  `ConfigPaths.files()` searches for `mammouth.jsonc`/`mammouth.json`/`opencode.jsonc`/
  `opencode.json` (project root, walking up)".
- Ebd. Z. 382 (Verdikt MM-3) zitiert die konkrete Fork-Quelle
  `…/packages/opencode/src/config/paths.ts:10-45`.

Damit ist belegt, dass Mammouths Loader `mammouth.json` im Projekt-Root liest — die
gepinnte Wahl ist korrekt und quellenbelegt, nicht bloß „wahrscheinlich". Die
JSONC-mit-Kommentaren-in-`.json`-Konstellation ist durch Fork-Parität abgedeckt:
Opencode shippt bereits Kommentare in `opencode.json` produktiv (lenient JSONC-Parser
unabhängig von der Endung). OQ-1 ist daher **kein Blocker**; es sollte vor Merge als
PINNED mit Verweis auf die obige Audit-Evidenz umformuliert werden (siehe MINOR-2),
statt die Verifikation zu deferren. Die Restunsicherheit ist ohnehin ein
Ein-Zeilen-Config-Diff ohne Code-Impact (R-3), für einen M-Tier-Config-Fix tragbar.

## Findings nach Severity

**MINOR-1 (Dimension: Konsistenz).** §3.2 begründet den Byte-for-byte-Erhalt von
`MAMMOUTH.settings-template.json` mit „surface-version v1 / kein
mcp-config.surface-formats". Der reale Guard in `apply_settings_surface_shape`
(`context.py:1348`) dispatcht aber auf `mcp-config.format != "opencode-json-v2"`, nicht
auf surface-version/surface-formats. Ergebnis identisch (Mammouth = `opencode-json`),
aber die Begründung ist ungenau. Vorschlag: Formulierung auf den tatsächlichen
`format != "opencode-json-v2"`-Guard umstellen.

**MINOR-2 (Dimension: Fehlende/ungeprüfte Annahmen).** OQ-1 ist durch
`docs/analysis/2026-09-30-provider-audit-docs-part2.md:341–342,382`
(Quelle `paths.ts:10-45`) bereits belegt. Vorschlag: OQ-1 von „offen" auf „gepinnt, Quelle:
Provider-Audit part2 §5.2 / MM-3" umstellen; die Pre-Merge-Realinstall-Verifikation bleibt
als optionale Bestätigung, blockiert aber nichts.

**INFO (Dimension: Risiken).** JSONC-Kommentare in einer `.json`-Datei: durch
bestehende Opencode-`opencode.json`-Produktivnutzung gedeckt; kein eigenes Finding,
nur zur Dokumentation. Falls gewünscht, könnte die Spec explizit auf `mammouth.jsonc`
ausweichen — nicht nötig, da Parität gegeben.

**Keine** critical- oder major-Findings.

## Vollständigkeits-/Spec-Mode-Checks (§7.1)

- Pflichtsektionen vollständig: Problem/Ziel/Nicht-Ziele (§1), Betroffene Dateien (§2),
  Interface Contracts (§3), Datenfluss (§4), Acceptance Criteria (§5), Test Plan (§6),
  Risiken (§7), Offene Fragen (§8). ✓
- Acceptance Criteria ≥ 1 pro Issue: #852 → AC-1/AC-2, #853 → AC-3/AC-4,
  #857 → AC-5/AC-6, + Regression AC-7. ✓
- Trace-Anker gesetzt und als vom Plan referenzierbar deklariert. ✓
- Approval-Marker vorhanden und konsistent (`status: proposed`, Gate-Hinweis Z. 10). ✓
- Keine unaufgelösten Platzhalter (TODO/TBD/`<…>`/`{{…}}`) in Pflichtsektionen. ✓
- Provider-agnostisch: jede Änderung ist reine Config-Daten; alle drei Code-Pfade
  (`apply_model_format`, `_init_provider_settings_json`, `_update_json_config`,
  `validate_mcp_document`) sind verifiziert generisch, kein Provider-Namen-Branch. ✓
- Dokumentierte Alternativen/Trade-offs: Nicht-Ziele (§1) und OQ-2/OQ-3 wägen bewusst
  nicht-gewählte Optionen (isolation-dirs, Reaktivierungs-Cleanup, model-catalog) ab. ✓

## Verdikt + Begründung

**APPROVED.**

Alle drei gepinnten Entscheidungen sind gegen den realen Code korrekt und nutzen
ausschließlich bereits produktive, generische Mechanismen (Parität zu KimiCode bzw.
Opencode). Sämtliche Vorher/Nachher-Snippets und Zeilenreferenzen stimmen mit dem
aktuellen Dateistand überein. Die einzige als offen markierte Frage (OQ-1) ist durch
bestehende Quellcode-Analyse im Repo (`provider-audit-docs-part2 §5.2`, Quelle
`paths.ts:10-45`) belegt und damit kein Blocker; die beiden MINOR-Findings sind reine
Präzisierungen der Spec-Prosa, keine inhaltlichen Mängel. Vollständigkeit, Logik,
Feasibility und Konsistenz sind gegeben.

**Empfehlung für den Autor (nicht blockierend):** MINOR-1 und MINOR-2 vor der
Implementierung in der Spec nachziehen (OQ-1 pinnen, §3.2-Begründung korrigieren).

Pipeline: `quality_pipelines.concept-driven-dev` schreitet fort (specify → review →
**approve** → plan). Der abgeleitete Plan MUSS den Trace-Anker
`SPEC-852-MAMMOUTH-PROVIDER-FIXES-2026-10-06` referenzieren.
