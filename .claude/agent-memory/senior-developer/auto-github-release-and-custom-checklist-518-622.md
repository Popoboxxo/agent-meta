---
name: auto-github-release-and-custom-checklist-518-622
description: DONE (not committed) — auto-github-release PostToolUse hook + custom pre-release checklist, both via conventions-presets extension
metadata:
  type: project
---

Issues #518 + #622 (+ nachgereichte custom-checklist-Anforderung) umgesetzt, NICHT committed (git-Agent trailt PR-URL). Kombiniert über die bestehende Conventions-Preset-Infrastruktur aus #521.

**Why:** #622 Fehlerfall — Release-Agent pusht Tag, vergisst `gh release create` → Tag ohne GitHub-Release. Strukturell gelöst statt Prosa-Härtung; release.md-Automatik-Teil unangetastet.

**How to apply:**
- Neuer Hook `hooks/1-generic/auto-github-release.sh` (PostToolUse/Bash, enabled_by_default:false) + reine Logik in `scripts/lib/auto_github_release.py`. Erkennt `git push <remote> <tag>` (nur wenn `git` das führende Token ist — `echo git push` triggert nicht), matcht Tag gegen `versioning.tag_format` (Regex mit optionalem Pre-Release-Tail), idempotent via `gh release view`, `--prerelease` bei Suffix-Tags. Opt-in: `conventions.release.github_release.enabled`. Fail-open, exit 0 immer.
- Neues Preset-Feld `release.github_release` + `release.custom_checklist` in allen 3 Presets (`config/conventions-presets.yaml`).
- custom_checklist → neuer Renderer `_render_release_custom_checklist` + Key `RELEASE_CUSTOM_CHECKLIST_BLOCK` in `render_convention_block`, registriert in `consistency/placeholders.py` _BUILTIN_VARS.
- **release.md byte-identity trick:** neuer Convention-Block-Platzhalter ersetzt die EXISTIERENDE Leerzeile nach der Checklisten-Tabelle (net-zero Zeile), sonst gäbe leer→"" eine doppelte Leerzeile. Convention-Blocks rendern live (config.py + standalone.py via render_convention_block), brauchen KEINEN standalone.py-Fallback (anders als [[new-block-placeholder-coupling]]).
- Schema: `conventions` ist additionalProperties:true, `hooks` erlaubt beliebige Namen → keine schema-Änderung nötig.

Achtung: `.meta-config/project.yaml` hatte beim Start eine fremde, unverwandte Working-Tree-Änderung (se-cascade-Kommentare entfernt) — NICHT Teil dieser Arbeit, git-Agent muss sie ausschließen.
