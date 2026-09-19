# Worktree-Preflight — Dynamic-Routing Template-Slimming

- **Task:** Task 1 — Working-Tree-Isolation-Gate
- **Vorhaben:** `docs/plans/2026-09-19-dynamic-routing-template-slimming-plan.md`
- **Branch:** `feat/dynamic-routing-template-slimming`
- **HEAD:** `deb115aa714e93f1d51cd2a2583597b1b226adc2` (`fix: compose mammouth override from generic base (#819)`)
- **Datum:** 2026-09-19
- **Agent:** git

## 0. Geltungsbereich / Nicht-Ausgeführt

Dieser Report ist **read-only Bestandsaufnahme**. Ausgeführt wurde ausschließlich:
`git status --porcelain=v1`, `git diff --stat`, `git diff --numstat`, `git ls-files --others`, `git diff` (lesend).

**Nicht ausgeführt (per Dispatch-Constraint):** kein `commit`, kein `push`, kein `stash`, kein `checkout`, kein `reset`, kein `add`.
Damit ist **Task-1-Step 4** („Commit nur des Reports …") **bewusst nicht ausgeführt** und an User/Orchestrator eskaliert.

## 1. Rohbefund `git status --porcelain=v1`

```text
 M .meta-config/generated-file-hashes.json
 M CHANGELOG.md
 M agents/1-generic/orchestrator.md
 M config/provider-capabilities.yaml
 M docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md
 M scripts/lib/agent_sync.py
 M scripts/lib/consistency/placeholders.py
 M scripts/lib/delegation_syntax.py
 M scripts/lib/standalone.py
 M scripts/lib/variables.py
 M tests/test_provider_agnostic_dispatch.py
 M tests/test_routing_tool_definitions.py
?? docs/plans/2026-09-19-dynamic-routing-template-slimming-plan.md
?? docs/specs/2026-09-19-dynamic-routing-template-slimming-final-rereview.md
?? docs/specs/2026-09-19-dynamic-routing-template-slimming-rereview.md
?? docs/specs/2026-09-19-dynamic-routing-template-slimming-review.md
?? docs/specs/2026-09-19-dynamic-routing-template-slimming.md
```

**Zählung:** 12 modified (worktree, nichts staged) + 5 untracked. Kein File ist im Index vorgemerkt (`git add` wurde nicht ausgeführt).

## 2. Rohbefund `git diff --stat`

```text
 .meta-config/generated-file-hashes.json            |  6 +-
 CHANGELOG.md                                       |  9 +++
 agents/1-generic/orchestrator.md                   | 18 +++--
 config/provider-capabilities.yaml                  | 21 ++++++
 ...09-06-issue-674-phase4b-harness-dependencies.md | 15 +++--
 scripts/lib/agent_sync.py                          |  5 ++
 scripts/lib/consistency/placeholders.py            |  2 +
 scripts/lib/delegation_syntax.py                   | 11 ++++
 scripts/lib/standalone.py                          |  3 +
 scripts/lib/variables.py                           |  2 +-
 tests/test_provider_agnostic_dispatch.py           | 20 ++++++
 tests/test_routing_tool_definitions.py             | 77 ++++++++++++++++++++++
 12 files changed, 172 insertions(+), 17 deletions(-)
```

`git diff --numstat`:

```text
3	3	.meta-config/generated-file-hashes.json
9	0	CHANGELOG.md
11	7	agents/1-generic/orchestrator.md
21	0	config/provider-capabilities.yaml
9	6	docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md
5	0	scripts/lib/agent_sync.py
2	0	scripts/lib/consistency/placeholders.py
11	0	scripts/lib/delegation_syntax.py
3	0	scripts/lib/standalone.py
1	1	scripts/lib/variables.py
20	0	tests/test_provider_agnostic_dispatch.py
77	0	tests/test_routing_tool_definitions.py
```

## 3. Inventar + Zuordnung (gehört zum Vorhaben ja/nein)

| # | Datei | Status | Plan-Ziel-Datei? | Gehört zu diesem Vorhaben? | Task-Owner | Blockierend |
|---|-------|--------|------------------|----------------------------|------------|-------------|
| 1 | `.meta-config/generated-file-hashes.json` | M | nein | nein (fremd) | — | nein |
| 2 | `CHANGELOG.md` | M | nein | nein (fremd) | — | nein |
| 3 | `agents/1-generic/orchestrator.md` | M | **JA** | nein (fremd, Vorbestand) | **Task 6** (+ Task 14 Dateisatz) | **JA** |
| 4 | `config/provider-capabilities.yaml` | M | nein | nein (fremd) | — | nein |
| 5 | `docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md` | M | nein | nein (fremd) | — | nein |
| 6 | `scripts/lib/agent_sync.py` | M | **JA** | nein (fremd, Vorbestand) | **Task 10** | **JA** |
| 7 | `scripts/lib/consistency/placeholders.py` | M | nein | nein (fremd) | — | nein |
| 8 | `scripts/lib/delegation_syntax.py` | M | nein | nein (fremd) | — | nein |
| 9 | `scripts/lib/standalone.py` | M | nein | nein (fremd) | — | nein |
| 10 | `scripts/lib/variables.py` | M | nein | nein (fremd) | — | nein |
| 11 | `tests/test_provider_agnostic_dispatch.py` | M | nein | nein (fremd) | — | nein |
| 12 | `tests/test_routing_tool_definitions.py` | M | **JA** | nein (fremd, Vorbestand) | **Task 4** | **JA** |
| 13 | `docs/plans/2026-09-19-…-plan.md` | ?? | nein (Plan selbst) | **ja** (dieses Vorhaben) | — | nein |
| 14 | `docs/specs/2026-09-19-…-slimming.md` | ?? | nein | **ja** (dieses Vorhaben) | — | nein |
| 15 | `docs/specs/2026-09-19-…-review.md` | ?? | nein | **ja** (dieses Vorhaben) | — | nein |
| 16 | `docs/specs/2026-09-19-…-rereview.md` | ?? | nein | **ja** (dieses Vorhaben) | — | nein |
| 17 | `docs/specs/2026-09-19-…-final-rereview.md` | ?? | nein | **ja** (dieses Vorhaben) | — | nein |
| 18 | `docs/plans/2026-09-19-…-worktree-preflight.md` | neu | nein (dieses Artefakt) | **ja** (dieses Vorhaben) | Task 1 | nein |

> Die 12 modified Dateien bilden einen **inhaltlich zusammenhängenden Fremd-Workstream** „route_intent runtime gating (Issue #264)": `ROUTE_INTENT_CALLABLE`-Gate in `agent_sync.py`/`variables.py`/`delegation_syntax.py`, Capability `route_intent_tool` in `provider-capabilities.yaml`, Orchestrator-§3-Fallback, zugehörige Tests + CHANGELOG + Hash-Regen. Dieser Workstream ist **semantisch benachbart** zu Block A, aber nach Plan-Kontext **nicht Scope dieses Vorhabens**.

## 4. Plan-Ziel-Überschneidungen (blockierend)

Drei der elf in der Plan-„Geänderte Dateien"-Liste genannten Modify-Dateien sind bereits fremd-dirty:

### 4.1 `agents/1-generic/orchestrator.md` → Task 6 (Orchestrator-Fallback-Contract)
- Fremd-Delta: Version `8.0.0 → 8.1.0`, neuer `{{#if ROUTE_INTENT_CALLABLE}}`-Zweig in §3 „Intent routing" inkl. Fallback-Prosa, mehrere Prosa-Anpassungen (`route_intent` → „route_intent bzw. abgeleitete Routing-Regel").
- Konfliktlage: Der Fremd-Hunk liegt exakt in `@@ -89,16 +89,20 @@` — also in dem §3-Block, den **Task 6** um den `name_index`-Fallback-Contract erweitert. Direkte Textüberlappung, **hohes Konfliktrisiko**.

### 4.2 `tests/test_routing_tool_definitions.py` → Task 4 (Config-Schema activation_groups + Addressability)
- Fremd-Delta: 77 neue Zeilen — `test_has_route_intent_tool_defaults_false_for_every_provider`, `test_build_provider_vars_route_intent_callable_defaults_false`, `_render_intent_routing_section`, zwei §3-Rendering-Tests.
- Konfliktlage: Task 4 muss in derselben Datei den Patternless- und Validator-Test migrieren; Fremd-Delta hängt ausschließlich am Dateiende an → Konflikt wahrscheinlich auf den Appended-Bereich begrenzt, aber Datei ist nicht isoliert.

### 4.3 `scripts/lib/agent_sync.py` → Task 10 (Config-Wiring + Block-Snippet-Loader)
- Fremd-Delta: 5 neue Zeilen in `_build_provider_vars` (`ROUTE_INTENT_CALLABLE`).
- Konfliktlage: Task 10 ändert dieselbe Datei (Migration des Rollen-Gate-Aufrufs). Im Plan-Risiko 1 **nicht namentlich antizipiert** → Eskalationsfall „andere Ziel-Datei" (Task-1-Akzeptanz).

### 4.4 Nicht betroffen
`scripts/lib/roles.py`, `config/role-defaults.yaml`, `scripts/lib/delegation_table.py`, `scripts/lib/agents.py`, `scripts/lib/config.py`, `scripts/lib/frontmatter.py`, alle `se-*`/`knowledge-*`/übrigen `1-generic`/`2-platform`-Templates, `snippets/orchestrator/*.md`, `tests/test_no_role_routes_in_templates.py`, `tests/test_se_role_boundary.py`, `tests/test_knowledge_engine.py` sind **clean** und startklar.

## 5. Empfehlungen je Überschneidung (ohne Ausführung)

> Grundregel: fremde Änderungen **niemals** in eigene Commits aufnehmen. Commit-Regel `git add <exakte Pfade>` gilt global.

| Datei | Empfehlung | Begründung |
|-------|------------|------------|
| `agents/1-generic/orchestrator.md` | **BLOCK** (Task 6 anhalten) → Fremdänderung durch User/Orchestrator **separat committen lassen** (nicht `stash`), danach Task 6 auf dem neuen Stand fortsetzen (Rebase-by-continuation). `skip` nicht sinnvoll: Datei ist Pflicht-Output von Task 6. `merge` erst nach Trennung. | Fremd-Workstream ist kohärent, getestet und shippable; er sollte committed, nicht versteckt werden. Direkte §3-Überlappung. |
| `tests/test_routing_tool_definitions.py` | **BLOCK** (Task 4 anhalten) → Fremdänderung **separat committen**, dann Task 4. Alternativ `stash` nur nach expliziter User-Freigabe; `skip` scheidet aus (Task 4 muss die Datei laut File-List migrieren). | Fremd-Tests decken `route_intent_tool`-Capability ab; ein `stash` würde sie aus dem Baum entfernen und die Hash-/Test-Lage inkonsistent machen. |
| `scripts/lib/agent_sync.py` | **BLOCK** (Task 10 anhalten) → Fremdänderung **separat committen**, dann Task 10. | Andere Ziel-Datei als im Plan-Risiko namentlich genannt → Eskalation, aber gleiche Lösung wie 4.1/4.2. |

**`stash`-Gesamtbewertung:** nicht empfohlen als Default. Der 12-Dateien-Satz ist ein zusammenhängender, potentiell release-fähiger Workstream; Einzel-`stash` über 12 Pfade riskiert Verlust der Nachvollziehbarkeit. Präferiert: **separater Fremd-Commit** durch den Eigentümer (User/Orchestrator), danach Fortsetzung dieses Vorhabens. Entscheidung liegt bei User/Orchestrator.

## 6. Blockade-Aussage

**Blockiert: JA.** Der Working Tree ist für den Plan-Ziel-Scope nicht isoliert.

- **Direkt blockiert (Plan-Ziel-Datei fremd-dirty):**
  - **Task 4** — `tests/test_routing_tool_definitions.py`
  - **Task 6** — `agents/1-generic/orchestrator.md`
  - **Task 10** — `scripts/lib/agent_sync.py` *(zusätzlich; im Plan-Risiko 1 nicht namentlich genannt → Eskalation)*
- **Transitiv blockiert (Depends-on-Kette):**
  - Task 5 (Depends on Task 4)
  - Task 7 (Depends on Task 4, Task 5)
  - Task 9 (Depends on Task 5, Task 10)
  - Task 11 (Barrier, Depends on Task 4/6)
  - damit der **kritische Pfad Block A** ab Task 4.
- **Nicht blockiert / startklar:** Task 2 (Snippet-Pre-Flight), Task 3 (`roles.py` clean), Task 8 (Depends on Task 2).

**Erforderliche Aktion (User/Orchestrator):** die drei Fremd-Überschneidungen (`orchestrator.md`, `test_routing_tool_definitions.py`, `agent_sync.py`) vor Fortsetzung von Task 4/6/10 separat committen oder explizit stashen lassen. Erst danach Task 4 → Task 5 → Task 6/10 → Task 11 fortsetzen.
