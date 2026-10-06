---
spec-id: SPEC-852-MAMMOUTH-PROVIDER-FIXES-2026-10-06
title: Mammouth Provider Fixes — model-format, settings_file, mcp-config — Mini-Spec
status: APPROVED
related-issue: "#852"
instances: ["#853", "#857"]
---

# Mammouth Provider Fixes — Spec
> Status: APPROVED (2026-10-06) — Review: `docs/specs/2026-10-06-852-mammouth-provider-fixes-review.md`. Approval-Marker maschinenlesbar (Frontmatter `status: APPROVED`); Approval-Gate §7.1 erfüllt.
> Trace-Anker: `spec-id: SPEC-852-MAMMOUTH-PROVIDER-FIXES-2026-10-06`; ein abgeleiteter Plan MUSS diesen Wert referenzieren.
> Provider-agnostic: jede Änderung ist reine Config-Daten (`config/ai-providers.yaml`); kein Code verzweigt auf einen Provider-Namen. `apply_model_format`/`validate_mcp_document`/`_init_provider_settings_json` lesen ausschließlich Config-Keys.

## 1. Problem / Ziel / Nicht-Ziele

**Problem.** Drei verwandte Mammouth-Provider-Bugs/-Lücken in `config/ai-providers.yaml` (Mammouth-Block, Zeilen 483–563), alle durch Live-Prüfung des generierten Zustands gegen Mammouths tatsächliches Laufzeitverhalten verifiziert:

1. **#852** — `model-format: "{model}"` lässt den Provider-Präfix weg; Mammouths Runtime erwartet `provider/model-id` (z. B. `mammouth/claude-sonnet-5`), erhält aber den bloßen Modellnamen.
2. **#853** — `settings_file: .mammouth/settings.json` wird von `_init_provider_settings_json()` (`scripts/lib/context.py:1365`) erzeugt, aber Mammouths nativer Loader liest diese Datei nie — er erwartet eine `mammouth.json` im Projekt-Root (OpenCode-Fork-Konvention, analog zu Opencodes eigenem `opencode.json`). Die generierte Datei ist inert.
3. **#857** — `mcp-config: {}` ist der einzige leere `mcp-config`-Eintrag in der gesamten Registry; jeder andere Provider (Claude, Gemini, Opencode, Continue, Codex, ZCode, KimiCode, Copilot) hat ein reales `committed-file`/`format`-Paar. Für Mammouth werden dadurch nie MCP-Artefakte geschrieben, obwohl `mcp-remote-transport: url` in `config/provider-capabilities.yaml:229` bereits MCP-Erwartungen andeutet.

**Ziel.** Alle drei Lücken config-only schließen, ohne neue Code-Pfade — jede Lösung nutzt einen bereits existierenden, generischen (Provider-Namen-freien) Mechanismus, der für andere Provider bereits produktiv ist.

**Nicht-Ziele.**
- Kein neuer Code in `scripts/lib/` — `apply_model_format()` (`scripts/lib/roles.py:326`), `_init_provider_settings_json()` (`scripts/lib/context.py:1365`) und der `opencode-json`-MCP-Writer (`scripts/lib/mcp_provider_config.py:260`) sind bereits vollständig generisch und brauchen keine Änderung.
- Kein `isolation-mechanism` für Mammouth (bliebe unverändert fehlend — Hard-Block-Isolation ist ein separates, unverifiziertes Feature, nicht Teil von #852/#853/#857).
- Keine `settings_local_file`/`settings_local_template` für Mammouth (kein anderer Provider außer Claude hat ein lokales Overlay-Template; nicht angefordert).
- Kein `model-catalog` für Mammouth (optional, von keinem der drei Issues verlangt; der Containment-Check in `model_contracts.py` bleibt ohne Katalog deaktiviert — konsistent mit Claude/Opencode).
- Kein Verhalten für Provider-Deaktivierung/-Reaktivierung von `mammouth.json` (siehe Offene Fragen — bestehender Opencode-spezifischer Mechanismus in `tests/test_provider_reactivation_artifacts.py` ist hart auf `"opencode.json"` codiert, nicht generisch; eine Mammouth-Parität dafür ist nicht Teil dieses Fixes).

## 2. Betroffene Dateien

| Datei | Art | Grund |
|---|---|---|
| `config/ai-providers.yaml` | ändern | Mammouth-Block: `model-format`, `settings_file`, `settings_template`, `capabilities`, `gitignore_entries`, `mcp-config` |
| `templates/configs/MAMMOUTH.settings-template.json` | neu | Settings-Skeleton für `mammouth.json` (Pendant zu `OPENCODE.settings-template.json`) |
| `config/provider-capabilities.yaml` | ändern | `special_notes` des Mammouth-Eintrags (Zeile 250) nennt explizit "MCP-Integration … nicht konfiguriert" — wird nach #857 falsch, muss aktualisiert werden |
| `tests/test_provider_hooks_config.py` | ändern | Zeile 31 pinnt den alten `settings_file`-Wert `.mammouth/settings.json` |
| `tests/test_model_contracts.py` | ändern/neu | Drei bestehende Assertions vergleichen bisher den unformatierten Mammouth-Tier-Wert (Zeilen 76–80, 133–137, 204–208); neuer Test für Single-Prefix-Kontrakt |

5 Dateien — M-Tier, config-only.

## 3. Interface Contracts

### 3.1 `config/ai-providers.yaml` — Mammouth-Block (vollständiger Diff der betroffenen Keys)

**Vorher** (Zeilen 489–531, Auszug):
```yaml
    model-format: "{model}"
    ...
    has_settings: true
    settings_file: .mammouth/settings.json
    capabilities:
    - agents
    - rules
    - hooks
    - commands
    - settings
    - snippets
    - skills
    - context-managed-block
    artifact_dir: .mammouth/artifacts
    checkpoint_dir: .meta-viz
    isolation-dirs:
    - .mammouth/
    bash_tool_name: bash
    provider_root_dirs:
    - .mammouth/
    gitignore_entries:
    - .mammouth/pending-tasks.md
    mcp-config: {}
    skills_dir: .mammouth/skills
```

**Nachher:**
```yaml
    # #852: Mammouth (OpenCode fork) resolves models at runtime as
    # "<provider>/<model-id>" (e.g. "mammouth/claude-sonnet-5"); a bare ID
    # is rejected. model-tiers/model-aliases below stay bare — apply_model_format()
    # (scripts/lib/roles.py) applies this prefix exactly once at emission,
    # the same mechanism KimiCode's "kimi-code/{model}" already uses.
    model-format: "mammouth/{model}"
    ...
    has_settings: true
    # #853: Mammouth's native loader reads mammouth.json at the project root
    # (OpenCode-fork convention, mirroring Opencode's own opencode.json) —
    # never .mammouth/settings.json, which was inert (never read).
    settings_file: mammouth.json
    settings_template: templates/configs/MAMMOUTH.settings-template.json
    capabilities:
    - agents
    - rules
    - hooks
    - commands
    - settings
    - snippets
    - skills
    - context-managed-block
    - mcp
    artifact_dir: .mammouth/artifacts
    checkpoint_dir: .meta-viz
    isolation-dirs:
    - .mammouth/
    bash_tool_name: bash
    provider_root_dirs:
    - .mammouth/
    gitignore_entries:
    - .mammouth/pending-tasks.md
    - .mammouth/mcp.local.json
    # #857: real MCP surface, mirrored from Opencode's own v1 shape (flat
    # top-level `mcp` key) — Mammouth is an explicit OpenCode fork (see
    # comments elsewhere in this block, e.g. commands_dir/#807) and
    # "opencode-json" is a generic format key (validate_mcp_document /
    # scripts/lib/mcp_provider_config.py), never a provider-name branch.
    # Same committed-file as the settings_file fix above: one JSON document
    # carries both general settings and the "mcp" key.
    mcp-config:
      committed-file: mammouth.json
      secrets-file: .mammouth/mcp.local.json
      format: opencode-json
    skills_dir: .mammouth/skills
```

No other key in the Mammouth block changes (`model-tiers`, `model-aliases`, `agent-transform`, `context_file`, `has_rules`, `has_hooks`, `has_commands`, etc. stay byte-identical).

### 3.2 `templates/configs/MAMMOUTH.settings-template.json` (new file, full content)

Mirrors the structure of `templates/configs/OPENCODE.settings-template.json` (JSONC, lenient-parsed by `scripts/lib/io.py::read_json_lenient`), re-branded for Mammouth and without the Opencode-only `subagent_depth`/`default_agent` v2-surface keys (Mammouth stays `surface-version: "v1"` with no `mcp-config.surface-formats`, so `apply_settings_surface_shape()` never touches this file — content is emitted byte-for-byte):

```json
{
  // Mammouth configuration (OpenCode fork)
  //
  // Managed by agent-meta:
  //   Agents  : .mammouth/agents/   (generated by sync.py)
  //   Commands: .mammouth/commands/ (generated by sync.py)
  //   Rules   : AGENTS.md           (embedded by sync.py)

  // Personal instructions — loaded locally, never committed (gitignored)
  // Copy howto/configs/AGENTS.personal-template.md → AGENTS.personal.md to use
  // "instructions": ["AGENTS.personal.md"],

  // Model override — comment out to use Mammouth's default
  // "model": "mammouth/claude-sonnet-5",

  // MCP servers
  // "mcp": {}
}
```

### 3.3 `config/provider-capabilities.yaml` — Mammouth `special_notes` (line 250)

**Vorher:**
```yaml
      - "Hooks-Pfade sind konfiguriert (.mammouth/hooks), aber ungespiegelt: kein verifiziertes hook_protocol (#630). MCP-Integration in ai-providers.yaml nicht konfiguriert."
```
**Nachher:**
```yaml
      - "Hooks-Pfade sind konfiguriert (.mammouth/hooks), aber ungespiegelt: kein verifiziertes hook_protocol (#630). MCP-Integration seit #857 konfiguriert (mcp-config.format: opencode-json, committed-file: mammouth.json)."
```

### 3.4 `tests/test_provider_hooks_config.py` — line 31

**Vorher:**
```python
    assert mammouth.get("settings_file") == ".mammouth/settings.json"
```
**Nachher:**
```python
    assert mammouth.get("settings_file") == "mammouth.json"
```
(Rest of the test — `hooks_dir` assertion, the two `!=` Claude-collision assertions — unchanged; `"mammouth.json" != claude["settings_file"]` still holds.)

### 3.5 `tests/test_model_contracts.py` — three existing assertions + one new test

Lines 76–80 (`test_ai_providers_model_tiers_beat_active_preset`):
```python
    resolved = _resolve("Mammouth", "senior-developer")
    assert resolved == f"mammouth/{registry_tier}", (
        "ai-providers.yaml model-tiers must win over the preset global fallback: "
        f"expected {registry_tier!r} (formatted), got {resolved!r}"
    )
```

Lines 133–137 (`test_provider_without_preset_entry_falls_back_to_registry`):
```python
    resolved = _resolve("Mammouth", "senior-developer")
    assert resolved == f"mammouth/{registry_tier}", (
        "without a preset provider-specific entry the registry model-tiers must "
        f"win: expected {registry_tier!r} (formatted), got {resolved!r}"
    )
```

Lines 204–208 (`test_project_local_preset_tiers_beat_ai_providers_model_tiers`):
```python
    resolved = _resolve("Mammouth", "senior-developer", config)
    assert resolved == f"mammouth/{local_powerful}", (
        "a project-local preset's tiers map must beat ai-providers.yaml "
        f"model-tiers: expected {local_powerful!r} (formatted), got {resolved!r}"
    )
```

New test, mirroring `test_kimicode_emits_single_prefix` (after line 227):
```python
def test_mammouth_emits_single_prefix() -> None:
    """#852: every resolved Mammouth ID carries exactly one ``mammouth/``
    prefix (idempotent model-format, no doubled prefix)."""
    resolved = _resolve("Mammouth", "orchestrator")
    assert resolved.startswith("mammouth/"), (
        f"Mammouth IDs must be namespaced, got {resolved!r}"
    )
    assert "mammouth/mammouth/" not in resolved, (
        f"model-format must be applied exactly once, got doubled prefix {resolved!r}"
    )
    assert resolved.count("mammouth/") == 1, (
        f"exactly one prefix expected, got {resolved!r}"
    )
```

## 4. Datenfluss

1. **Modell-Resolution (#852):** `resolve_model()` (`scripts/lib/roles.py:349`) löst einen Tier/Alias/Override zu einer rohen Modell-ID auf (z. B. `claude-sonnet-5`, unverändert bare in `model-tiers`) → `apply_model_format()` liest `provider_config["Mammouth"]["model-format"]` (neu: `"mammouth/{model}"`) → gibt `mammouth/claude-sonnet-5` zurück → dieser Wert landet im generierten Agenten-Frontmatter (`model:`-Feld) unter `.mammouth/agents/*.md`. Persistenz: generierte Agent-Dateien (git-getrackt).
2. **Settings-Init (#853):** `_init_provider_settings_json()` (`scripts/lib/context.py:1365`, aufgerufen aus `_sync_opencode_context()` wegen `_shares_context_with_embedded_rules` — Mammouth teilt `AGENTS.md` mit Opencode) liest `pc["settings_file"]` (neu: `mammouth.json`, Projekt-Root) → Datei existiert nicht → liest `pc["settings_template"]` (neu gesetzt) → rendert `templates/configs/MAMMOUTH.settings-template.json` via `substitute()` → schreibt `mammouth.json` im Projekt-Root. Persistenz: `mammouth.json` (git-getrackt, da `gitignore.settings` standardmäßig `false` ist).
3. **MCP-Config (#857):** Wenn MCP-Server im Projekt deklariert sind, merged der generische `opencode-json`-Writer (`scripts/lib/mcp_provider_config.py:260`, `_update_json_config` mit `mcp_key="mcp"`) die Server-Einträge als flaches Top-Level-`mcp`-Objekt in dieselbe `mammouth.json` — read-modify-write, alle anderen Top-Level-Keys (inkl. der von #853 initial geschriebenen Kommentare/Werte) bleiben erhalten. Secrets (API-Keys etc.) gehen stattdessen nach `.mammouth/mcp.local.json` (`mcp-config.secrets-file`, neu in `gitignore_entries`, also nie committed). Persistenz: `mammouth.json` (committed), `.mammouth/mcp.local.json` (gitignored).
4. **Validierung:** `check_model_contracts()` (`scripts/lib/consistency/model_contracts.py:92`) prüft nach jedem Sync, dass jede emittierte Mammouth-`model:`-ID mit dem Präfix `mammouth/` beginnt und nicht doppelt vorkommt. `validate_mcp_document()` (`scripts/lib/artifact_validate.py:328`) prüft `mammouth.json` gegen das `opencode-json`-Schema, sobald die Datei existiert.

## 5. Acceptance Criteria

**AC-1 (#852).** Given `config/ai-providers.yaml` mit `Mammouth.model-format: "mammouth/{model}"`, when `python scripts/sync.py` für ein Projekt mit aktivem Mammouth-Provider läuft, then jede Datei unter `.mammouth/agents/*.md` trägt im Frontmatter `model: mammouth/<bare-id>` (z. B. `model: mammouth/claude-sonnet-5`), nie den bloßen Modellnamen.

**AC-2 (#852).** Given eine bereits formatierte Modell-ID als expliziter Override (`model-overrides.Mammouth.<role>: "mammouth/claude-sonnet-4-6"`), when resolved, then das Ergebnis trägt genau einen `mammouth/`-Präfix (kein `mammouth/mammouth/`-Doppel) — geprüft durch `test_mammouth_emits_single_prefix` und `check_model_contracts()`.

**AC-3 (#853).** Given ein frisches Projekt ohne existierende `mammouth.json`, when `sync.py` für Mammouth initialisiert, then wird `mammouth.json` im Projekt-Root (nicht unter `.mammouth/`) aus `templates/configs/MAMMOUTH.settings-template.json` erzeugt, und `.mammouth/settings.json` wird nicht mehr geschrieben.

**AC-4 (#853).** Given eine bestehende `mammouth.json` mit Fremdinhalt (z. B. manuell vom Nutzer ergänzte Keys), when `sync.py` erneut läuft, then bleibt die Datei unverändert (`_init_provider_settings_json` überschreibt eine existierende Datei nie — `log.skip(..., "already exists — not overwritten")`).

**AC-5 (#857).** Given MCP-Server im Projekt deklariert (`.meta-config/mcp-servers.yaml` o. ä., aktiver Mammouth-Provider), when `sync.py` läuft, then enthält `mammouth.json` ein Top-Level-`mcp`-Objekt mit den konfigurierten Servern, und Secrets erscheinen ausschließlich in `.mammouth/mcp.local.json`, welches in `.gitignore` gelistet ist.

**AC-6 (#857).** Given keine MCP-Server deklariert, when `sync.py` läuft, then wird kein `mcp`-Key in `mammouth.json` erzwungen (kein leeres `"mcp": {}`-Rauschen) — Verhalten identisch zu Opencode mit leerer Server-Liste.

**AC-7 (Regression, alle drei).** `python3 scripts/sync.py --validate` meldet für Mammouth keine `model-contract`- oder `mcp`-Findings in einem frisch synchronisierten Projekt mit aktivem Mammouth-Provider.

## 6. Test Plan

- **Unit (angepasst):** `tests/test_provider_hooks_config.py::test_mammouth_has_its_own_hooks_dir_and_settings_file` — Assertion auf `"mammouth.json"` (§3.4).
- **Unit (angepasst):** `tests/test_model_contracts.py` — drei bestehende Assertions auf `f"mammouth/{...}"` umgestellt (§3.5); sonst würden sie mit dem neuen `model-format` fehlschlagen (sie vergleichen aktuell den unformatierten Registry-Wert).
- **Unit (neu):** `tests/test_model_contracts.py::test_mammouth_emits_single_prefix` — Single-Prefix-Kontrakt, mirrored von `test_kimicode_emits_single_prefix` (§3.5), deckt AC-1/AC-2.
- **Bestehende Suite, unverändert erwartet grün:**
  - `tests/test_model_contracts.py` (restliche KimiCode-/Claude-Tests) — kein Mammouth-spezifischer Code-Pfad geändert.
  - `tests/test_gitignore_provider_dirs.py` — generisch über `settings_file`-Key, kein hartcodierter Pfad für Mammouth.
  - `tests/test_provider_three_file_invariant.py`, `tests/test_provider_config_contracts.py`, `tests/test_context_agents_md_idempotency.py`, `tests/test_agents_md_shared_context_convergence.py`, `tests/test_rules_skill_channel.py` — keine Mammouth-`settings_file`/`model-format`/`mcp-config`-Literale gefunden (verifiziert per Grep vor Spec-Erstellung).
  - `tests/test_mcp_config.py`, `tests/test_sync_validation_gate.py`, `tests/test_artifact_contracts.py` — testen das `opencode-json`-Format generisch über ein `mcp`-Dict-Fixture, nicht providergebunden; kein Mammouth-Literal betroffen.
- **Manuell / End-to-End:** `python3 scripts/sync.py` in einem Scratch-Projekt mit `ai-providers: [Mammouth]` ausführen, dann:
  1. `grep '^model:' .mammouth/agents/*.md` → jede Zeile beginnt mit `model: mammouth/`.
  2. `test -f mammouth.json && ! test -f .mammouth/settings.json`.
  3. `cat mammouth.json` → enthält den Header-Kommentar aus §3.2.
  4. `python3 scripts/sync.py --validate` → Exit-Code 0, keine `model-contract`/`mcp`-Findings.
- **Validate-Gate:** `python3 scripts/sync.py --validate` muss repo-weit grün bleiben (DoD, `.claude/rules/dod-criteria.md`).

## 7. Risiken

- **R-1 (model-format-Breaking-Change):** Jedes bereits generierte Mammouth-Agent-Frontmatter mit dem alten bloßen Modellnamen wird beim nächsten Sync auf den präfixierten Wert aktualisiert — für Projekte, die agent-meta als Submodul einbinden und bereits einen Mammouth-Provider aktiv haben, ist das ein sichtbarer, aber intendierter Diff (kein Datenverlust, reine Korrektur). Mitigation: in der PR-Beschreibung explizit als Breaking-Fix markieren.
- **R-2 (settings_file-Pfadwechsel):** Eine bereits existierende `.mammouth/settings.json` aus einem alten Sync-Lauf wird NICHT automatisch entfernt (kein Cleanup-Code für den alten Pfad in diesem Fix — Nicht-Ziel). Sie bleibt als verwaistes File liegen, bis ein Nutzer sie manuell löscht. Akzeptiert für diesen P2/P3-Fix; keine Baseline-Migration verlangt von den drei Issues.
- **R-3 (MCP-Format-Annahme):** `mcp-config.format: opencode-json` ist eine begründete, aber nicht runtime-verifizierte Analogie (Mammouth = OpenCode-Fork laut Code-Kommentaren, kein eigener MCP-Schema-Nachweis aus der Mammouth-Doku vorliegend). Sollte sich das Format bei echter Mammouth-Nutzung als abweichend erweisen, ist nur `format`/`committed-file` in `config/ai-providers.yaml` zu ändern — kein Code betroffen (siehe Offene Frage OQ-1).
- **R-4 (Doppel-Schreiber auf `mammouth.json`):** Settings-Init (#853) und MCP-Merge (#857) schreiben in dieselbe Datei, aber zu unterschiedlichen Zeiten (Init nur bei Abwesenheit, Merge als Read-Modify-Write) — dasselbe Muster wie bei Opencodes `opencode.json`, bereits produktiv und getestet (`tests/test_mcp_config.py`). Kein neues Kollisionsrisiko.

## 8. Offene Fragen + Risiken

- **OQ-1:** Ist `mammouth.json` (statt `.mammouth.json`, `mammouth.jsonc` oder tatsächlich `opencode.json`) der exakte Dateiname, den Mammouths Binary liest? Die Ausgangs-Issue nennt "mammouth.json(c) / opencode.json" als Alternativen, ohne sich endgültig festzulegen. Diese Spec pinnt `mammouth.json` als wahrscheinlichste, mit der restlichen Konvention (eigene `.mammouth/`-Namespace, kein Vermischen mit einem echten Opencode-Provider im selben Projekt) konsistente Wahl — **Eskalationsvorschlag:** vor Merge einmalig gegen eine echte Mammouth-Installation verifizieren (Real-Repo-Test analog zu den `UNVERIFIED`-Markierungen, die im Mammouth-Block bereits für `context_adapter` existieren); falls falsch, ist die Korrektur ein Ein-Zeilen-Config-Diff.
- **OQ-2:** Soll `mammouth.json` beim Deaktivieren des Mammouth-Providers automatisch entfernt werden (Parität zu Opencodes Reaktivierungs-Artefakt-Handling in `tests/test_provider_reactivation_artifacts.py`, welches aktuell hart auf `"opencode.json"` codiert und nicht generisch ist)? Nicht Teil von #852/#853/#857 — als Folge-Issue vorgeschlagen, falls gewünscht.
- **OQ-3:** Soll `isolation-dirs` für Mammouth um `mammouth.json` ergänzt werden (Parität zu Opencodes `isolation-dirs: [.opencode/, opencode.json, AGENTS.md]`)? Aktuell folgenlos, da Mammouth kein `isolation-mechanism` gesetzt hat (Hard-Block-Isolation ist für Mammouth insgesamt noch nicht aktiv) — als Nicht-Ziel markiert, aber bei künftiger Aktivierung von `isolation-mechanism` zu berücksichtigen.
