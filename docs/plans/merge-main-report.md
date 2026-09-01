# Merge Report — beide Fix-Branches auf main (#514)

STATUS: done
RESULT: Beide Fix-Branches sauber auf `main` gemergt. Verifikations-Gate bestanden (Exit 0, 583 Tests grün). Kein Push, kein PR (nur lokal).

## Ausgangslage

- Base beider Branches: `2965e363` (`chore: release v0.101.0-beta.3`)
- Working Tree war NICHT clean: uncommittete lokale Änderungen in
  `.meta-config/project.yaml`, `config/generated/model-registry.json`,
  `config/tier-presets.yaml` (Model-Overrides geleert, `model-inherit-main-chat`,
  Registry-/Tier-Anpassungen). Diese gehören zu keinem der Fix-Branches und
  wurden **reversibel gestasht** (siehe Stash-Hinweise unten), nicht committet.
- `docs/plans/issue-546-report.md` (untracked) wurde nicht angefasst.

## Merge-Strategie je Konflikt

### Merge 1: `fix/issue-546-compact-lossless` → `6ea8f28e`
- **Keine Konflikte** — sauberer no-ff Merge (19 Dateien, 88+/30-).

### Merge 2: `fix/admin-ui-remote-token` → `91ca1260`
- **Konflikte ausschließlich in REGENERIERTEN Dateien (7 Stück):**
  - `.claude/agents/agent-meta-manager.md`, `.gemini/agents/agent-meta-manager.md`,
    `.mammouth/agents/agent-meta-manager.md`, `.opencode/agents/agent-meta-manager.md`
  - `.meta-config/context-hashes.json`, `CLAUDE.md`, `MAMMOUTH.md`
  - **Strategie:** keine manuelle Auflösung — je Datei eine Seite genommen
    (`git checkout --ours`), Merge committet, danach `python3 scripts/sync.py`
    zur konsistenten Regeneration ausgeführt. Ergebnis als eigener Commit
    `chore: regenerate context files post-merge` (6 Dateien, 6+/6-).
- **Quell-Dateien — automatisch gemerged, keine Konflikte:**
  - `tests/test_context_compact_mode.py`: automatischer Merge kombinierte BEIDE
    Zusätze korrekt — Retention-Anchors aus #546 (`_MANDATORY_ANCHORS`,
    `test_compact_mode_shrinks_and_preserves_mandatory_anchors`, Zeile 348/386)
    UND admin-ui-Marker (`"admin-ui": "## Troubleshooting"`, `## Host-Bindung +
    Token-Regeln`, `.claude/skills/admin-ui/SKILL.md`). Verifiziert per
    `git grep` — keine Hälfte verloren.
  - `CHANGELOG.md`: fix/admin-ui-remote-token enthält KEINEN CHANGELOG-Eintrag
    (leerer Diff `main...fix/admin-ui-remote-token`), daher nichts zu
    kombinieren — nur der #546-Eintrag (aus Merge 1) bleibt.
  - `scripts/lib/context.py`, `scripts/admin-server.py`, `config/rules-presets.yaml`
    u. a.: automatisch gemerged, keine Konflikte.

## Finale Commit-Liste (`git log --oneline main -8`)

```
f434c989 chore: regenerate context files post-merge
91ca1260 Merge branch 'fix/admin-ui-remote-token'
6ea8f28e Merge branch 'fix/issue-546-compact-lossless'
a36fe176 docs: add admin-ui token fix report
ed0a301b fix: transport admin-ui token to remote API calls
0fb4d22e fix: lossless compact mode retains stack/build values
2965e363 chore: release v0.101.0-beta.3
2cd46963 chore: release v0.101.0-beta.2
```

## Verifikations-Gate (auf main)

| Check | Ergebnis |
|---|---|
| `python3 scripts/sync.py --validate` | **Exit 0** — "[PASS] All checks passed" (2 bekannte Warnings: orchestrator-strict ohne Hook-Support für Opencode/Gemini) |
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q --ignore=tests/browser` | **583 passed in 279.83s (0:04:39)** — 0 failed |

## Stash-Hinweise (nicht Teil des Merges)

- `stash@{0}` — von mir erstellt: `wip: local model-registry/tier-preset adjustments (pre-merge)`
  (die oben genannten uncommitteten Änderungen). Reversibel; NICHT automatisch
  wieder angewendet, um den main-Zustand nicht zu verunreinigen. User kann den
  Stash bei Bedarf manuell anwenden/verwerfen.
- `stash@{1}` — bereits vor dem Auftrag vorhanden, nicht angefasst:
  `wip: full-mode toggle from admin-ui test (max_lines, auto_generate)`.

## Artefakte

- Merge-Commits: `6ea8f28e`, `91ca1260`
- Regenerate-Commit: `f434c989`
- HEAD: `f434c989ca1d1223068050e3dfd91021cb8e89fe`
