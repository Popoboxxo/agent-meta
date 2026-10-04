# auto_commit Commit-Authority vs. tatsächliche Permissions — Spec
> Status: Entwurf | Issue: #767 | verwandt: #694, #706

## Problem / Ziel / Nicht-Ziele
Unter opencode mit `auto_commit.mode: auto` entstehen keine inkrementellen Commits; sie
werden am Task-Ende gebatcht.

**Root Causes (mit Beleg):**
1. `scripts/lib/auto_commit.py:14` (`_ELIGIBLE_TOOLS = {"Edit","Write"}`) und
   `is_role_eligible()` (`:32-39`) prüfen **nur** Edit/Write, **nicht** Bash. Der
   `orchestrator` (Tools `[TodoWrite, Agent, Read, Write]`, `agents/1-generic/orchestrator.md:7-12`)
   und `documenter` (Read/Write/Edit, kein Bash) gelten damit als commit-eligible.
2. `render_auto_commit_block()` (`auto_commit.py:85-169`) rendert für **jede** Rolle
   identisch „Commit directly as soon as ANY trigger is true". Der Block ist eine
   **globale** Variable (`scripts/lib/config.py:1302-1315`, in `_build_core_variables`,
   Funktionskopf `config.py:1172`), identisch in jedes Template mit
   `{{#if AUTO_COMMIT_ENABLED}}` substituiert (`orchestrator.md:335-336`).
3. Der `orchestrator` hat unter opencode `permission.bash: deny`
   (`docs/analysis/evidence/2026-09-30-runtime-opencode-v2.md:63-67`) und kann den Befehl
   gar nicht ausführen → widersprüchliche Anweisung; Git wird bis zum Workflow-Ende
   delegiert → Batching.
4. Die Fähigkeitsprüfung ist zu grob: „Write ohne Bash" bedeutet **nicht** zwingend
   „kann an `git` delegieren". Die meisten schreibfähigen Doku-/Konzept-Rollen
   (`documenter`, `copyeditor`, `technical-writer`, `concept-architect`,
   `concept-specifier`, se-*) haben **weder** Bash **noch** das `Agent`/`Task`-Tool
   (`_tools_can_spawn`, `scripts/lib/agent_sync.py:65-85`) und können daher **gar nicht**
   committen — weder direkt noch per Delegation. Sie brauchen einen dritten Pfad
   (`notify`): Dateiliste + fertige Commit-Message in den Report, damit der Aufrufer/
   Orchestrator committet.

**Ziel:** Rolle-bewusste Commit-Authority mit **vier** Fähigkeitsklassen
(`direct` / `delegate` / `notify` / `none`), die exakt die tatsächliche Tool-Fähigkeit
abbilden. `eligible_roles` (Guard-Allowlist) spiegelt nur echte Direkt-Commit-Fähigkeit.

**Nicht-Ziele:** opencode-Runtime-Hook/Plugin (advisory-by-design, s. Scope), Änderung
der Guard-Hook-Semantik, neue Provider-Branches, Template-/`{{#if}}`-Änderungen.

## Entscheidungen (ADR)
**Kontext:** Zwei Commit-Anweisungen („direkt committen" für alle) widersprechen dem
opencode-Permission-Modell; eine reine Boolean-Eligibility ist zu grob, weil
„schreibfähig" drei operative Fähigkeiten verdeckt.

**Entscheidung (Option a):** Authority ist eine **abgeleitete, provider-agnostische
Fähigkeitsklassifikation** aus dem 1-generic-`tools:`-Contract, kein handgepflegter
Rollenkatalog und kein Provider-Branch:

| Authority | Bedingung (aus `tools:`) | Verhalten am Trigger-Boundary |
|-----------|--------------------------|-------------------------------|
| `direct`  | `Bash` ∧ (`Edit` ∨ `Write`) — Bash **und** (Edit und/oder Write) | committet selbst (`git add`/`commit`) |
| `delegate`| `{Edit,Write}` ∧ ¬`Bash` ∧ spawn-fähig (`Agent`∨`Task`) | delegiert den Commit an `git` |
| `notify`  | `{Edit,Write}` ∧ ¬`Bash` ∧ ¬spawn-fähig | führt kein Git aus; liefert geänderte Dateien + fertige Conventional-Commit-Message im Result/Report |
| `none`    | sonst (kein Write)       | leerer Block |

Beispiele (belegt am Frontmatter): `developer`/`tester`/`se-developer` (Bash+Write) →
`direct`; `orchestrator` (Agent+Write, kein Bash) → `delegate`; `documenter`/
`copyeditor`/`technical-writer`/`concept-architect`/`concept-specifier` (Write, kein
Bash, kein Agent) → `notify`; `explorer`/`git` (kein Write) → `none`.

**Konsequenzen:** `eligible_roles` bleibt **direct-only** (nur `direct`-Rollen dürfen
laut Guard-Hook selbst committen). `delegate`-Rollen lösen den Commit am Trigger über
den `git`-Agenten aus; `notify`-Rollen committen nie, sondern reichen die Message nach
oben durch. Der Template-Platzhalter `AUTO_COMMIT_BLOCK` bleibt unverändert; die
Unterscheidung entsteht ausschließlich in der Rollen-Overlay-Logik des Syncs.

## Interface Contracts
- `auto_commit.py:is_role_eligible(role, agent_meta_root, platform=None) -> bool`
  **Neu:** True nur bei `Bash` **und** (`Edit` **oder** `Write`) — also
  `Bash` ∧ (`Edit` ∨ `Write`), nicht `Edit` ∧ `Write`. `git`/`explorer` bleiben
  False. Basis bleibt das 1-generic-Frontmatter (`tools:`), provider-agnostisch.
- `auto_commit.py:role_commit_authority(role, agent_meta_root, platform=None) -> Literal["direct","delegate","notify","none"]`
  **Neu.** `platform=None` aus Symmetrie zu `is_role_eligible` (`_template_path`,
  `auto_commit.py:19-29`). Ermittlung:
  - kein Write (weder `Edit` noch `Write`) → `"none"`
  - `Bash` ∧ (`Edit` ∨ `Write`) → `"direct"`
  - (`Edit` ∨ `Write`) ∧ ¬Bash ∧ spawn-fähig → `"delegate"`
  - (`Edit` ∨ `Write`) ∧ ¬Bash ∧ ¬spawn-fähig → `"notify"`
  Spawn-Fähigkeit = `Agent` oder `Task` in `tools` (oder `*`), konsistent mit
  `agent_sync._tools_can_spawn` (`agent_sync.py:65-85`). Um einen Import-Zyklus zu
  vermeiden, darf `auto_commit.py` das Prädikat lazy importieren oder spiegeln —
  der Contract ist die Semantik, nicht der Importpfad.
- `auto_commit.py:render_auto_commit_block(resolved, authority="direct") -> str`
  **Erweitert.** Modus domininiert die Authority (siehe Contract weiter unten):
  - `mode == "off"` → `""` (unabhängig von `authority`)
  - `mode == "suggest"` → **dieselbe** propose-only-Prosa für **jede** Authority
  - `mode == "auto"`:
    - `direct` → bestehende „Commit directly as soon as ANY …"-Prosa
    - `delegate` → neue Delegate-Prosa: Trigger-Boundary benennen, Commit an den
      `git`-Agenten delegieren, `git push/tag/branch` ausdrücklich dem `git`-Agenten
      überlassen
    - `notify` → neue Notify-Prosa: geänderte Dateien + fertige, Conventional-Commits-
      konforme Message in den eigenen Result/Report aufnehmen; **kein** `git commit`,
      **keine** Delegation
    - `none` → `""`
  - `mode == "custom"`:
    - `direct` → bestehende custom-Prosa (`custom_script`, Sentinel-Präfix)
    - `delegate` → Delegate-Prosa, die den `custom_script`-Exit als Entscheidungstor
      nennt („delegate to `git` when `<script>` exits 0")
    - `notify` → Notify-Prosa, die den `custom_script`-Exit als Entscheidungstor nennt
      (Dateiliste + Message in den Report; kein Git)
    - `none` → `""`
- **`secret_scan` (F1):** Die konfigurierte Secret-Scan-Anforderung
  (`secret_scan: true`, Default) wird in **jede** Schreib-Authority weitergegeben:
  `direct` führt den Scan selbst vor dem Commit aus; `delegate` verlangt ihn von der
  Partei, die den Commit ausführt (Delegations-Empfänger); `notify` verlangt ihn vom
  Aufrufer/Orchestrator, bevor die gemeldete Message committet wird. Ein Fund blockiert
  den Commit. Bei `secret_scan: false` entfällt die `delegate`/`notify`-Anforderung;
  der `direct`-Zweig behält seinen expliziten „disabled"-Hinweis. `suggest` rendert nie
  eine Scan-Zeile (authority-agnostisch, propose-only).
- **Fail-closed (F4):** ein unbekannter oder `None`-`authority`-Wert wird als
  `"none"` behandelt und rendert `""`; der Default-Parameter `authority="direct"`
  bleibt unverändert (nur ungültige explizite Werte werden herabgestuft).
- `config.py:_build_core_variables` legt `variables["_AUTO_COMMIT_RESOLVED"]` ab
  (Präzedenz: `_INTENT_ROUTING_TOOL_DEFS`) statt nur den globalen Text; Auto-commit-
  Variablen liegen im Block `config.py:1302-1315` innerhalb `_build_core_variables`
  (Funktionskopf `config.py:1172`).
- `agent_sync.py:sync_agents_for_provider` überschreibt pro Rolle
  `merged_vars["AUTO_COMMIT_BLOCK"]` und `merged_vars["AUTO_COMMIT_ENABLED"]` direkt
  nach Zeile `1337` (dort ist `role` bekannt; `merged_vars` wird bereits pro Rolle
  gebaut, `substitute` in `:654`):
  ```
  authority = role_commit_authority(role, agent_meta_root)
  if resolved.mode == "off":
      merged_vars["AUTO_COMMIT_ENABLED"] = "false"   # Mode-Gate gewinnt IMMER
      merged_vars["AUTO_COMMIT_BLOCK"]   = ""
  else:
      merged_vars["AUTO_COMMIT_ENABLED"] = "true"
      merged_vars["AUTO_COMMIT_BLOCK"]   = render_auto_commit_block(resolved, authority)
  ```
- `AUTO_COMMIT_BLOCK` bleibt der einzige Template-Platzhalter — **keine** Template-/
  `{{#if}}`-Änderungen.

## Datenfluss
1. `load_config` → `auto_commit` (mode/triggers/…).
2. `build_variables`: `render_auto_commit_block(...)` global (Default `direct`, dient
   nur als Fallback für Pfade außerhalb des Rollen-Overlays) + `_AUTO_COMMIT_RESOLVED`
   in den Variablen.
3. `sync_pipeline._sync_stage_auto_commit_allowlist` (`sync_pipeline.py:1479-1494`)
   schreibt `eligible_roles` = nur `direct`-Rollen in
   `.meta-config/auto-commit-allowlist.json`.
4. Pro Rolle im Agent-Loop (`agent_sync.py:1324-1347`, Overlay nach `:1337`):
   `role_commit_authority` → `AUTO_COMMIT_BLOCK`/`AUTO_COMMIT_ENABLED` rollen-spezifisch
   überschreiben → `substitute` (`:654`). **Off-Gate hat Vorrang vor jeder Authority.**
5. Guard-Hook (`hooks/1-generic/orchestrator-guard-impl.sh:201-232`) liest die Allowlist
   unverändert (trust-only). `delegate`-/`notify`-Rollen stehen nicht drin und brauchen
   den Sentinel nicht, da `git` (bzw. der Aufrufer) committet.

### Mode × Authority Matrix (maßgeblich)
| mode \ authority | direct | delegate | notify | none |
|---|---|---|---|---|
| `off` | `""` | `""` | `""` | `""` |
| `suggest` | propose-only | propose-only | propose-only | `""` |
| `auto` | direct-Prosa | delegate-Prosa | notify-Prosa | `""` |
| `custom` (script ok) | custom-Prosa | delegate-Prosa (script-Gate) | notify-Prosa (script-Gate) | `""` |
| `custom` (script fehlt) | config-error-Prosa | config-error-Prosa | config-error-Prosa | `""` |

> `secret_scan: true` (Default) ergänzt in `auto`/`custom` für `direct`/`delegate`/
> `notify` die Secret-Scan-Anforderung (Rollen je nach Authority, s. Contract oben);
> `suggest` und `off` rendern nie eine Scan-Zeile.

## Acceptance Criteria
1. **(Direct-Eligibility)** `is_role_eligible(role, …)` ist True für
   `developer`/`tester` (Bash+Write) und False für `orchestrator`/`documenter`/
   `concept-architect`/`technical-writer`/`copyeditor`/`git`/`explorer`.
2. **(Authority-Klassifikation)** `role_commit_authority(…)` liefert: `developer`/
   `tester`/`se-developer` → `"direct"`; `orchestrator` → `"delegate"`;
   `documenter`/`copyeditor`/`technical-writer`/`concept-architect`/`concept-specifier`
   → `"notify"`; `explorer`/`git` → `"none"`. `platform=None` ist zulässig.
3. **(Allowlist direct-only)** `resolve_auto_commit_config` mit
   `active_roles=[orchestrator, developer, git, tester]` liefert in **allen** Modi
   `eligible_roles == ["developer","tester"]`.
4. **(direct-Prosa, mode-spezifisch)** Gerenderter `developer`-Agent (mode `auto`) enthält
   „Commit directly as soon as ANY"; (mode `custom`) enthält „Commit directly whenever".
5. **(delegate-Prosa, mode-spezifisch)** Gerenderter `orchestrator`-Agent (mode `auto`)
   enthält „delegate … `git`" und das Trigger-Boundary (nicht Task-Ende), verbietet
   `git push/tag/branch` und enthält **kein** „Commit directly".
6. **(notify-Prosa, mode-spezifisch)** Gerenderter `documenter`-Agent (mode `auto`)
   enthält die Notify-Anweisung (geänderte Dateien + fertige Conventional-Commit-Message
   im Result/Report) und enthält weder „Commit directly" noch eine `git`-Delegations-Aufforderung.
7. **(Off-Gate, alle Authorities)** Bei `mode == "off"` gilt für **jede** Rolle
   `AUTO_COMMIT_ENABLED == "false"` und `AUTO_COMMIT_BLOCK == ""`; in keinem
   `.claude|.gemini|.opencode/agents`-File erscheint der Block. Byte-Identität zum Sync
   ohne `auto_commit`-Key hält (Szenario 21).
8. **(suggest, authority-agnostisch)** Bei `mode == "suggest"` rendern `developer`
   (`direct`), `orchestrator` (`delegate`) und `documenter` (`notify`) **denselben**
   propose-only-Block; keiner enthält „Commit directly" oder eine `git`-Delegationsanweisung.
9. **(custom, no-Bash-Rollen)** Bei `mode == "custom"` erhält `orchestrator`
   (`delegate`) delegate-Prosa und `documenter` (`notify`) notify-Prosa, jeweils mit
   Nennung des `custom_script`; keiner enthält „Commit directly".
10. **(none)** Read-only-Rollen (`explorer`) sowie `git` enthalten **keinen**
    `AUTO_COMMIT_BLOCK`-Text.
11. **(Coverage)** Jede Rolle mit Schreibfähigkeit (`direct`|`delegate`|`notify`) hat
    `{{AUTO_COMMIT_BLOCK}}` im 1-generic-Template (expliziter Coverage-Test).
12. **(Allowlist-Pipeline)** Sync in ein tmp-Projekt schreibt `eligible_roles` ohne
    `orchestrator`.
13. **(Guard-Hook unverändert)** Sentinel `IS_ALLOWLIST_SENTINEL` wird weiter anhand der
    Allowlist vergeben — Semantik unverändert.

## Tests
- `tests/test_auto_commit_lib.py`: Fälle für alle vier Authorities ergänzen
  (`orchestrator`→delegate, `documenter`→notify, `explorer`→none); bestehende
  `eligible_roles`-Erwartung (`:83` `["developer","orchestrator","tester"]`) auf
  `["developer","tester"]` korrigieren.
- `tests/test_auto_commit_block_render.py`: `authority="direct"` vs `"delegate"` vs
  `"notify"` vs `"none"`; Mode × Authority Matrix (insb. `suggest` für alle Authorities
  identisch; `off` für alle leer).
- `tests/test_auto_commit_coverage.py`: **expliziter** Test, dass delegate- und
  notify-Rollen bei `mode != "off"` weiter einen Block erhalten (nicht stillschweigend
  schwächen, weil `is_role_eligible` nun direct-only ist). Coverage-Predikat auf
  „Write-fähig" (direct|delegate|notify) verbreitern.
- `tests/test_auto_commit_allowlist_pipeline.py`: `orchestrator not in eligible_roles`.
- `tests/test_orchestrator_guard_hook.py`: unverändert lassen (Regression-Nachweis).
- **Szenario-Configs (MINOR 7):** `tests/scenarios/configs/18-auto-commit.project.yaml`,
  `19-auto-commit-suggest.project.yaml`, `20-auto-commit-custom.project.yaml`,
  `21-auto-commit-off-ignores-config.project.yaml` — deren eingebettete Prüf-Zettel
  (`eligible_roles = ["developer","orchestrator","tester"]`) sowie die Assert-Files
  `tests/scenarios/asserts/18-*.sh` (`:61`), `19-*.sh` (`:67`), `20-*.sh` (`:61`),
  `21-*.sh` (`:74`) auf `["developer","tester"]` bzw. `["developer"]` (Szenario 20:
  nur `developer` direct) umstellen; Kommentare entsprechend angleichen. `orchestrator`
  entfällt aus `eligible_roles`, erhält aber in 18/19/20 weiterhin den
  delegate-/notify-Block (mode != off).
- **AC3 ist mode-spezifisch:** „Commit directly" darf nur in `auto`/`custom`-Prosa
  vorkommen; in `suggest` nie.

## Offene Fragen + Risiken
- OQ-1 **(entschieden):** `suggest` ist authority-agnostisch — für **alle** Authorities
  wird die bestehende propose-only-Prosa gerendert (kein „direkt committen", keine
  Delegationsanweisung); der User/Orchestrator entscheidet. Keine offene Frage mehr.
- Risiko: Rollen mit Bash aber ohne Write (z. B. `git`) bleiben `none` — korrekt, eigener
  Pfad (volle Commit-Authority via Bash + eigener Sentinel).
- Risiko: Plattform-Override könnte `tools:` ersetzen; bereits in `auto_commit.py:19-27`
  als out-of-scope dokumentiert.
- Risiko: `notify`-Rollen „verlieren" den Commit, wenn der Aufrufer die Message nicht
  aufgreift. Bewusst: sie committen nie selbst; die Message ist der Contract.

## Scope-Grenzen
OUT: opencode Runtime-Hook/Plugin, das Trigger **mechanisch** auslöst. auto_commit ist
bewusst prompt-advisory auf allen Providern ohne Runtime-Dispatch-Gate
(`subagent_permissions.py:1-7`, `docs/superpowers/plans/2026-09-08-auto-commit-tiers.md`) —
ein solcher Gate ist ein separates Feature (eigene Spec). Der Claude-Guard-Hook-Sentinel
bleibt Claude-only und anderswo harmlos. Keine Template-/`{{#if}}`-Änderungen.

## Version / CHANGELOG / Provider-Agnostik
- CHANGELOG-Eintrag unter Unreleased; Version-Bump gemäß `conventions`-Skill
  (scripts/lib-Änderung, keine Template-Änderung).
- Keine `if provider == …`-Verzweigung: Fähigkeit kommt aus dem Frontmatter-`tools:`-Contract
  (`provider-agnostic`-Skill).

## Trace-Anker
spec-id: SPEC-am-767-auto-commit-authority
