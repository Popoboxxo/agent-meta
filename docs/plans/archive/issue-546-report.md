# Issue #546 — Compact-Modus verlustfrei (Fix-Report)

## STATUS

**done** — alle 8 Plan-Schritte umgesetzt, Tests grün, commitet auf Feature-Branch.

## RESULT

Der Compact-Zweig von `templates/context/partials/project-metadata.md` löscht die
Sektionen Tech-Stack / Architektur / Build & Development nicht mehr. Statt des
verlustbehafteten `> Tech-Stack, Architektur & Build-Befehle: discoverable via Repo …`
werden die Werte jetzt als dichte Inline-Zeilen **erhalten**:

- `> Stack: {{RUNTIME}} · {{LANGUAGE}} · Deps: {{SYSTEM_DEPENDENCIES}}`
- `> Build: `{{BUILD_COMMAND}}` · Test: `{{TEST_COMMAND}}` · Dev: `{{DEV_STACK_START}}` · Reload: `{{DEV_STACK_RELOAD}}``
- `> Struktur: `.meta-config/project.yaml` → `variables.PROJECT_STRUCTURE`.` (Pointer, folded)
- `**Entry-Point:**` + `**Besondere Patterns:**` (KEY_PATTERNS) bleiben verbatim erhalten

Der Full-Modus bleibt **byte-identisch** zum Original (Verifiziert: `FULL_MODE_IDENTICAL: True` —
die zwei `{{#if COMPACT_MODE}}`-Blöcke wurden getrennt gehalten, Sektions-Reihenfolge
Tech-Stack → Architektur → Code-Konventionen → Build & Development → Anforderungs-Kategorien unverändert).

### Weitere Korrekturen

- `CHANGELOG.md` `[0.101.0-beta.1]`: falscher zlib+Base64-Claim entfernt; beschreibt jetzt
  `context_file.mode: compact` (instruction-preserving density, values retained). Der nie
  implementierte No-Op-Key `context_compress: true` wurde entfernt (Repo-weites grep: 0 Treffer).
- `schema.json` bleibt unverändert (dokumentiert `context_file.mode` bereits korrekt).
- `tests/test_context_compact_mode.py`: Wert-Retention-Anchors ergänzt (Stack/Build/Test/
  Entry-Point/Struktur-Pointer), Größenverhältnis-Schwelle von `>1.6` auf `>1.3` gesenkt.

### Verifikation

| Metrik | Vorher | Nachher |
|---|---:|---:|
| `pytest tests/ --ignore=tests/browser` | 581 passed / 2 failed | **583 passed / 0 failed** |
| `sync.py --validate` | — | Exit 0 |
| Targeted `test_context_compact_mode.py` | — | 39 passed / 0 failed |
| Red-Proof (Mutation `{{RUNTIME}}`→`XX-BROKEN`) | — | Test schlägt ✓ / nach Revert grün ✓ |

Die 2 Vorher-Failures (`test_committed_agents_md_equals_compact_render`,
`test_editing_only_the_notes_is_not_reported_as_drift`) waren **pre-existing**
(VERSION=0.101.0-beta.3, aber generierte Files stale auf beta.2). Der `sync.py`-Lauf
hat sie als Seiteneffekt aufgelöst.

## ARTIFACTS

- **Branch:** `fix/issue-546-compact-lossless`
- **Commit:** `0fb4d22e33097b9d22877d8757b049efeee54e5f` — `fix: lossless compact mode retains stack/build values` (Body enthält `Fixes #546`)
- **Geänderte Dateien (19):**
  - `templates/context/partials/project-metadata.md` (+13/−2)
  - `CHANGELOG.md` (+5/−4)
  - `tests/test_context_compact_mode.py` (+13/−2)
  - Regeneriert: `AGENTS.md` (+17/−2), `CLAUDE.md` (+19/−3), `MAMMOUTH.md` (+17/−2)
  - Version-Drift (beta.2→beta.3): `.meta-config/context-hashes.json` (+3/−3),
    12 Agent-Files (`agent-meta-manager`, `agent-meta-scout`, `meta-feedback` × Claude/Gemini/Opencode/Mammouth, je +1/−1)

## OFFEN / Notes

- Kein Push, kein PR, kein main-Commit (Branch bleibt lokal).
- Umgebung: global installiertes pytest-Plugin (homeassistant) bricht die Collection —
  alle pytest-Läufe benötigen `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Nicht Teil dieses Fixes.
- `rtk` CLI ist in dieser Umgebung nicht installiert — plain git verwendet.
