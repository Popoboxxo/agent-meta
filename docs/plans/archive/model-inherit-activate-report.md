# Report — Main-Chat Modell-Vererbung aktivieren

**Issue-Ref:** #514 (Report-Format) · **Datum:** 2026-08-29
**Branch:** `feat/model-inherit-main-chat-activate` (von `main` @ f434c989)
**Auftrag:** Generierte Agenten sollen das Main-Chat-Modell erben statt ein festes `model:` zu tragen.

---

## STATUS: done

## RESULT

Die Vererbungs-Implementierung **existiert bereits in `main`** — kein Neu-Bau nötig.
Aktiviert für den aktiven Provider **Opencode** (Main-Chat läuft auf
`opencode-go/deepseek-v4-flash`). Alle 53 generierten Opencode-Agenten tragen
kein `model:`-Feld mehr und erben das Main-Chat-Modell zur Laufzeit.

### Implementierungs-Nachweis (Code-Path, bereits gemerged)

| Komponente | Funktion | Verhalten |
|---|---|---|
| `scripts/lib/roles.py::resolve_model` (Z. 106–144) | Inherit-Branch | `model-inherit-main-chat[provider]` truthy → return `""` |
| `scripts/lib/agents.py::inject_model_field` (Z. 450–459) | Feld-Injektion | leeres Model → entfernt `model:`-Feld (Clean Slate) |
| `scripts/lib/agents.py` (Z. 1073–1078) | Continue-Guard | intentional `""` löst KEINEN role-defaults-Fallback aus |
| `scripts/lib/config.py::_validate_model_inheritance` (Z. 165+) | Hard-Validation | Typ-Check + Exklusivität vs. `model-override-all` → fail-fast Exit 1 |
| `scripts/admin-server.py` (`/api/model-inherit`, Z. 2612+) | Admin-UI Toggle | weigert Schreibzugriff bei Konflikt |

Merged via `05575666 feat: model-inherit-main-chat super-override (#524)` und
`2fe7e562 fix: model-inherit review findings (#525)` — beide in `main` enthalten.

### Config-Änderung (`.meta-config/project.yaml`)

```yaml
model-override-all: {}
model-inherit-main-chat:
  Opencode: true
```

- **Konflikt-Check:** `model-override-all` ist leer (`{}`) → keine Exklusivitäts-
  Verletzung, `_validate_model_inheritance` greift nicht (kein fail-fast).
- **Kein Dead-Config-WARN:** `model-overrides` existiert nur für `Gemini`
  (knowledge-*-Rollen); die Soft-Warnung feuert nur bei Overrides für den
  SELBEN Provider wie die Vererbung. Opencode hat keine per-Rolle-Overrides.
- **Gemini/Claude/Mammouth:** unverändert auf festen Modellen (bewusst —
  Vererbung ist per-Provider, Main-Chat-Provider ist Opencode).

### Sync + Validierung

| Schritt | Ergebnis |
|---|---|
| `python3 scripts/sync.py` | Exit 0 · 57 actions · 14 Warnings |
| Warning-Analyse | 13× external-tools drift (pre-existing, `.opencode/package.json`, plugins etc. — unabhängig), 1× `PIPELINE_DETAILS_DIR`-Placeholder (pre-existing) — **keine** inherit-bezogene Warnung |
| `python3 scripts/sync.py --validate` | Exit 0 · 2 Warnings (pre-existing orchestrator-strict no-hook-support für Opencode/Gemini) |

### Verifikation generierter Agenten

- `.opencode/agents/*.md`: **53/53 ohne `model:`-Feld** (`grep -L` = 53, `grep -l` = 0)
- Debug-Log: 53× `model-inherit-main-chat active for provider 'Opencode': omitting model field`
- Spot-Check (3 Files): `orchestrator`, `developer`, `senior-developer` — Frontmatter
  ohne `model:` ✓, `generated-from` unverändert
- `.claude/` (52), `.gemini/` (53), `.mammouth/` (53): unverändert mit festen Modellen

### Tests

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q --ignore=tests/browser
→ 583 passed in 273.94s  (0 failed)  — exakt erwartete Baseline
```

## ARTIFACTS

| Datei | Änderung |
|---|---|
| `.meta-config/project.yaml` | +2 Zeilen: `model-inherit-main-chat: {Opencode: true}` |
| `.opencode/agents/*.md` (53 Files) | je −1 Zeile (`model:` entfernt) |

Commit: `feat: activate main-chat model inheritance for opencode agents`

## OFFEN

- **Kein Push / kein PR** (per Auftrag) — Branch liegt lokal.
- **`stash@{0}`-Relevanz:** Der Stash (wip auf `fix/issue-546-compact-lossless`,
  pre-merge) enthält dieselbe Aktivierungs-Absicht (`model-inherit-main-chat:
  Opencode: true`) — **bestätigt** die gewählte Config-Syntax. Zusätzlich enthält
  er lokale model-registry/tier-presets-Anpassungen (u. a. `nano: opencode-go/mimo-v2.5`,
  neue Modell-IDs glm-5.3, grok-4.6, hy4-preview) sowie das Leeren der
  Gemini-knowledge-Overrides. **Nicht angewendet** (per Auftrag, nur inventarisiert).
  Für die Vererbung selbst sind die Registry/Tier-Inhalte NICHT erforderlich —
  aber bei einem späteren Sync ohne Stash bleiben die neuen Modell-IDs
  (mimo-v2.5 etc.) unregistriert; Relevanz nur, falls tier-presets angepasst
  werden sollen.
- **Optionaler Folge-Schritt:** Vererbung auch für Claude/Gemini/Mammouth aktivieren
  (`model-inherit-main-chat: {Claude: true, ...}`) — Trade-off: nur sinnvoll, wenn
  die jeweilige Plattform das Weglassen des `model:`-Feldes zur Laufzeit unterstützt;
  bei Claude Code ist das Feld-Omittieren etabliert, bei Gemini/Mammouth ungeprüft.
- **Restart-Hinweis:** KI-Session/IDE muss neu gestartet werden, damit die
  generierten Agenten (ohne `model:`) in die Laufzeit geladen werden (Sync-Output).