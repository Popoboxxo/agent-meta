---
pipeline_stages:
  implement: 1
status: DRAFT
revision: "1.3"
review: "2026-11-09 — RVW-1181-01 … -06 (§15) + RVW2-1181-01 … -05 + RVW2-X-01 (§15) + K1–K8 (§15.1)"
date: 2026-11-09
issue: "#1181"
spec: docs/specs/2026-11-09-commit-authority-grant-spec.md
spec-status: DRAFT
spec-revision: "1.3"
klasse: L
base-commit: aaed14c2
branch: feat/1181-commit-authority-grant
scenario-id: "94"
execution-order: "#1187 -> #1186 -> #1188 -> #1181 -> #1141"
trace:
  - SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09
  - SPEC-am-767-auto-commit-authority
  - issue-1181
---

# Projektseitiger Commit-Authority-Grant für Edit-only-Rollen (Issue #1181) — Implementation Plan

> **Status: DRAFT** — Dieser Plan implementiert nichts und committet nichts. Er ist die
> Umsetzungsplanung zur Spec `docs/specs/2026-11-09-commit-authority-grant-spec.md`
> (`Status: DRAFT`, Rev. 1.3, Klasse L).
>
> **Voraussetzung (Master-Rule `spec-plan-workflow`):** Die Spec trägt noch **kein**
> `Status: APPROVED`. Task-Ausführung startet erst, wenn `concept-reviewer`/der Nutzer die
> Spec freigegeben hat; dieser Plan kann parallel zum Review als Umsetzungsvorschlag dienen,
> ist aber selbst ungeprüft (`Status: DRAFT`).
>
> **Quellen:** Spec §1–§12 (Rev. 1.3); `.tmp/issue-dump/issue-1181.json` (maßgeblich),
> `issue-1142.json`, `issue-1151.json`, `issue-1172.json`; Baseline `baseline-validate.txt`
> (`EXIT=0`) und `baseline-check.txt` (fünf erwartete Vorab-Warnungen, kein `auto_commit`-Befund);
> Ist-Code mit `datei:zeile`-Ankern unten; Vorläufer
> `docs/specs/767-auto-commit-permission-authority.md` und
> `docs/superpowers/specs/2026-09-07-auto-commit-tiers-design.md`; Review 2026-11-09
> (RVW-1181-01 … -06 und RVW2-1181-01 … -05 + RVW2-X-01, in §15 aufgelöst).
>
> **Klasse:** L (Bounded, Review-Loop) · **Datum:** 2026-11-09 · **Base:** `aaed14c2`
> (`v2.0.0-beta.8`) · **Branch:** `feat/1181-commit-authority-grant` (Branch-Guard: keine
> Implementierung auf `docs/…`; der Plan-Branch dieser Datei ist ein Doku-Branch).
> **Aufwand:** 16 Tasks, 6 Meilensteine, 10 Produktionsdateien (1 neu:
> `scripts/lib/hook_state.py`; 1 Sicherheitsdatei geändert:
> `hooks/1-generic/orchestrator-guard-impl.sh`) + 5 Doku-Dateien, 9 Testdateien (6 erweitert,
> 3 neu) plus 1 Szenario-Config + 1 Assert-Script.
> Eine belastbare Schätzung liefert `effort-estimator` (Textverweis — hier bewusst nicht
> berechnet).
>
> **Größe je Task:** S ≤ 1 Datei/< 30 min · M 1–2 Dateien/< 90 min · L > 2 Dateien oder
> Integrations-/Verhaltensänderung über Modulgrenzen.
>
> **Ausführungsreihenfolge der Tasks:** T1 → **T15** → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 →
> **T16** → T10 → T11 → T12 → T13 → T14. T15 liefert das gemeinsame Hook-Prädikat, ohne das T2
> und T6 die Guard-Aktivierung nicht prüfen können; T16 härtet den Hook, nachdem das Artefakt
> (T9) `authority_overrides` trägt.
>
> **Querschnitt (verbindlich, aus dem Review):** Kanonische Issue-Reihenfolge
> `#1187 → #1186 → #1188 → #1181 → #1141`, Whitelist-Ableitung zuletzt. Szenario-IDs:
> **`94` = #1181** (bestätigt, letzte vergebene ID `93`, `tests/scenarios/registry.md:132`),
> **`95–98` = #1187**. `docs/issue-labels.md` (aus #1188) wird in **#1186** klassifiziert.
> Die gemeinsame Konfliktmatrix steht in §3a.

## 1. Zielbild in fünf Sätzen

1. Ein Projekt kann einer schreibfähigen Rolle **bewusst** Commit-Authority geben, ohne eine
   Datei unter `agents/` zu editieren — über den neuen, schema-validierten Key
   `auto_commit.authority_overrides.<role>` mit `authority: direct` **und** dem Pflicht-Ack
   `acknowledge_full_shell: true`.
2. Der Grant eskaliert ausschließlich `delegate`/`notify` → `direct`; er nimmt nichts zurück und
   ist niemals Default, sodass ein Sync ohne diesen Key bis auf die Allowlist-Version
   (`version: 2`, §3a/K-10) byte-identisch zu heute rendert.
3. Die Wirkung ist doppelt: die Rolle erscheint in `eligible_roles` (Hook-Sentinel) **und** ihr
   generierter Agent erhält `Bash` (Claude) bzw. `run_command` (Gemini) — aber nur auf Providern
   mit verifiziertem Hook-Protokoll **und** effektiv aktivem Guard-Hook. Opencode ist hook-los
   (`has_hooks: false`), erhält also **keine** positive Render-Erweiterung, sondern `bash: deny`
   plus WARN; positive `bash: allow`/`shell: allow`-Fälle laufen nur gegen einen synthetischen
   Hook-Fixture (K-12).
4. Jedes Schrumpfen von `eligible_roles` gegenüber der vorhandenen Allowlist erzeugt eine
   `sync.log`-Warnung mit Rollenliste **und** genau einem, disjunkt definierten Grund
   (`grant withdrawn`, `role removed`, `gate-dropped`, `no Bash`) — auch im Dry-Run.
5. Der Grant ist per Doku, Sync-Log und Allowlist-Artefakt (`version: 2`) auditierbar und
   ausdrücklich als **Shell-Rechteausweitung** dokumentiert, nicht als enges `git`-Recht; die
   Sentinel-Härtung begrenzt nur Sentinel-tragende Kommandos, nicht injizierte Befehle.

## 2. Klarstellungen (Plan-Präzisierung, Review-Stand 2026-11-09)

- **K-1 (`resolve_commit_grant` braucht `agent_meta_root`):** Die abgeleitete Klasse stammt aus
  `role_commit_authority(role, agent_meta_root)` (`scripts/lib/auto_commit.py:127-143`) und ist
  ohne Wurzel nicht bestimmbar. Signatur (in der Spec §4.3 nachgezogen):
  `resolve_commit_grant(role, resolved, provider_capabilities, agent_meta_root, *,
  guard_enabled: bool) -> tuple[str, bool]`. Beide Ergänzungen sind additiv; `guard_enabled`
  ist keyword-only, damit ein vergessener Parameter nicht still `False`/`True` wird.
- **K-2 (`active_roles` ist kein Violation-Parameter mehr):** Der Review-NIT ist so aufgelöst,
  dass der Parameter **nicht** tot bleibt: `authority_override_violations(config,
  agent_meta_root, provider_config=None)` prüft nur Härtefälle; die neue
  `authority_override_notices(config, active_roles)` liefert INFO für Grants auf inaktive Rollen
  (§3.5/§4.6 der Spec). Damit ist „Rolle nicht in `roles:`" sichtbar, aber weiterhin kein Fehler
  (Spec §4.2 Nr. 4) — der Tippfehler-Fall bleibt über die abgeleitete Authority `none` ein ERROR.
- **K-3 (`render_bash` ist False für abgeleitet-`direct`-Rollen):** `resolve_commit_grant`
  liefert für Rollen, die schon `Bash` im Template haben, `(direct, False)` — ihr Frontmatter
  bleibt unangetastet. `append_frontmatter_tools` ist zwar idempotent
  (`scripts/lib/frontmatter.py:206-208`), aber der Grant soll Rollen ohne `Bash` präzise
  adressieren und keine Render-Diffs für heute schon berechtigte Rollen erzeugen.
- **K-4 (Gemini-Tool-Name ist `run_command`, nicht `code_execution`):** `_map_claude_tools_to_gemini_tools`
  (`scripts/lib/provider_transform.py:854-870`) hat **keinen Aufrufer** (Beleg:
  `config/provider-capabilities.yaml:290` führt den toten Mapper selbst als offene Inkonsistenz).
  Der lebende Pfad ist datengetrieben: `agent-transform.tools: filter` +
  `tool-name-map.Bash: run_command` (`config/ai-providers.yaml:230-251`, Eintrag `:250`);
  `bash_tool_name: code_execution` (`config/ai-providers.yaml:203`) ist die
  Enforcement-/Hook-Seite. Tests **müssen** `run_command` asserten. In Spec Rev. 1.1 korrigiert
  (§3.3 + AC-2-Traceability), Finding F-4.
- **K-5 (disjunkte Schrumpf-Gründe, RVW-1181-04):** Die frühere Präzedenz
  (`grant withdrawn` → `gate-dropped` → `no Bash` → `role removed`) widersprach T9
  (`product-manager (role removed)`). Verbindlich ist jetzt die disjunkte Definition der Spec
  §3.5 mit der Reihenfolge `grant withdrawn` → `role removed` → `gate-dropped` → `no Bash`,
  wobei `no Bash` **nur** für Rollen gilt, die in `roles:` stehen. Das T9-Fixture muss deshalb
  `copyeditor`, `documenter` und `planner` in `roles:` führen und `product-manager` weglassen.
- **K-6 (Admin-UI: minimal-invasiv, Feld folgt als F-2):** `viewProjectAutoCommit` klont den
  Block (`docs/ui/admin-ui.html:7650`) und sendet beim Speichern ein **neues** Objekt
  (`:7753-7761`) — jeder unbekannte Key wird gelöscht. Ohne die Zwei-Zeilen-Korrektur würde
  jedes UI-Speichern den neuen Grant zerstören; deshalb ist der **Round-Trip-Erhalt** Teil
  dieses Plans (T10), das explizite Formularfeld bleibt F-2.
- **K-7 (`eligible_roles` bleibt mode-unabhängig):** Wie heute
  (`scripts/lib/auto_commit.py:261-263`) listet die Allowlist Capability, nicht Mode; der Hook
  gatet den Sentinel auf `auto`/`custom` (`hooks/1-generic/orchestrator-guard-impl.sh:464-478`).
  Ein Grant unter `mode: off`/`suggest` erscheint daher in `eligible_roles`, rendert aber
  **kein** `Bash` (`resolve_commit_grant` → `(direct, False)`).
- **K-8 (Grant-Wert ist ein Objekt, RVW-1181-02):** `authority_overrides.<role>` ist
  `{authority: direct, acknowledge_full_shell: true}`. Es gibt **keinen** Skalar-Kurzweg
  (`documenter: direct` ist ein Schema-Fehler). `normalize_authority_overrides()` ist die
  einzige Normalisierung nach `{role: "direct"}`; sie akzeptiert nur Einträge mit
  `authority == "direct"` **und** `acknowledge_full_shell is True`. Das Ack ist die
  Vertragsdokumentation der vollen Shell-Ausweitung (Spec §3.1/§3.3.1).
- **K-9 (Guard muss effektiv aktiv sein, RVW-1181-01):** Neues Modul
  `scripts/lib/hook_state.py` mit `resolve_hook_enabled(hooks_config, hook_stem,
  enabled_by_default=False) -> (enabled, invalid)` und `guard_hook_enabled(config)`;
  `hooks.sync_hooks` (`:621-626`) wird darauf umgestellt (verhaltens- und textgleich),
  `auto_commit` nutzt dasselbe Prädikat. Default des Guards ist `true`
  (`hooks/1-generic/orchestrator-guard.sh:7`); `hooks.orchestrator-guard.enabled: false`
  oder ein Nicht-Bool-Wert schaltet den Grant-Render ab (fail closed) und macht
  `--validate` rot.
- **K-10 (`ALLOWLIST_VERSION` 1→2 ist ein bewusster Default-Diff, NIT):** Jedes Consumer-Artefakt
  wird beim nächsten Sync neu geschrieben (`"version": 2` plus `"authority_overrides": {}`),
  auch ohne Grant. Das ist gewollt (eine Artefaktform, eine Versionsnummer) und wird in
  `CHANGELOG.md` unter „Changed“ sowie in §9 Migration genannt. Kein Consumer muss etwas tun:
  kein Leser prüft `version`, der Hook liest `mode`/`eligible_roles`/`authority_overrides`
  tolerant per `.get`.
- **K-11 (Sentinel-Härtung + Attributionslücke, RVW-1181-02):** Der Hook akzeptiert den Sentinel
  einer Grant-Rolle nur für ein Kommando, dessen Statements **alle** `git` sind und dessen
  Mutations-Scope `narrow` ist (alles andere rc 2). Das schließt den wohlgeformten Pfad, **nicht**
  den Injection-Pfad: das PreToolUse-Payload trägt nur ein opakes `agent_id`, keinen Rollennamen
  (`orchestrator-guard-impl.sh:262-269`, Sentinel-Parse `:326-350`). Deshalb bleibt der Grant ein
  Voll-Shell-Grant (Ack-Pflicht, K-8) und die Grenze wird nirgends als Security-Boundary
  dokumentiert. Finding F-5.
- **K-12 (Opencode ist kein positiver Render-Fall, RVW2-1181-01):** `config/ai-providers.yaml:274`
  (`has_hooks: false`) und `config/provider-capabilities.yaml:179` (`hooks: false`) machen die
  Bedingung „verifizierter Hook" für Opencode unerfüllbar. Ein Test, der auf einem echten
  Opencode-Sync `bash: allow`/`shell allow` erwartet, kann nie grün werden. Der einzige reale
  Opencode-Fall ist der Deny-Pfad (`bash: deny`/`shell: deny` + WARN); positive
  v1/v2-Permission-Tests laufen ausschließlich gegen einen synthetischen hook-fähigen
  `provider_capabilities`-Fixture (Form Claude/Antigravity).
- **K-13 (`config.py` prüft beide Verstoßklassen, RVW2-1181-03):** `_build_core_variables`
  (`scripts/lib/config.py:1806`) ruft heute nur `auto_commit_violations`. Der Fail-Safe-Zweig
  (`:1814-1821`) muss zusätzlich `authority_override_violations(config, agent_meta_root)`
  auswerten (inkl. `INVALID_CONFIG_MARKER` und `authority_overrides: {}`); sonst rendert ein
  Grant ohne Ack weiter, obwohl Spec §4.2 Nr. 1 den Fail-Safe verlangt.
- **K-14 (Mapping-Guard in `effective_commit_authority`, RVW2-1181-04):** Der Zugriff lautet
  `authority_overrides.get(role) if isinstance(authority_overrides, Mapping) else None`. Damit
  hält die Funktion ihren „wirft nie"-Vertrag auch dann, wenn ein Aufrufer (oder Test) eine
  Liste übergibt; `authority_override_violations` bleibt für die Meldung zuständig.
- **K-15 (Notice braucht die effektive aktive Menge, RVW2-1181-05):** `authority_override_notices`
  bekommt `{r for r in (ctx.active_set.raw_roles or ()) if ctx.active_set.has(r)}` — nicht
  `raw_roles` allein. Sonst erhält eine gate-dropped Rolle keine INFO-Zeile, obwohl Spec §4.3
  „dropped by the active set" ausdrücklich als inaktiv definiert.
- **K-16 (`agents/`-Prüfung ist commit-fest, RVW2-1181-02):** `git diff --stat agents/` ist nach
  dem Commit des Tasks leer und damit vakuum-grün. Alle Nachweise (M1-Gate, T14-Step 4, AC-1)
  verwenden `git diff --name-only aaed14c2..HEAD -- agents/`.
- **K-17 (Provider-/Guard-Gate ist Wirkbedingung, nicht Präzedenzstufe, Szenario-Konflikt K5):**
  Spec §4.2 listet sechs **Wertstufen**; das Gate steht als eigener Block „Post-Grant-Demotion"
  darunter, weil es einen bestehenden Grant nur herabstufen, nie setzen kann. Kein Task ändert
  dadurch seine Reihenfolge: T6/T8 prüfen das Gate weiterhin **nach** der Grant-Auflösung.
- **K-18 (Namensstil, Szenario-Konflikt K7):** Der neue Key heißt **`acknowledge_full_shell`**
  (snake_case), weil er innerhalb der bestehenden snake_case-Sektion `auto_commit` liegt
  (`file_count_threshold`, `custom_script`, `secret_scan`). Neue Top-Level-Sektionen der Welle
  bleiben kebab-case. Alle Schema-, Test-, Doku- und Meldungsstellen tragen den snake_case-Namen.
- **K-19 (Schema und `_KEYS` im selben PR, Szenario-Konflikt K8):** T1-Step 2 und T1-Step 3 sind
  **ein** Commit; ein Schema-Key ohne `_KEYS`-Eintrag (`scripts/lib/auto_commit.py:164`) lässt
  `auto_commit_violations()` „unknown key(s)" melden und deaktiviert per Fail-Safe die gesamte
  Authority — #1187 liefe weiter, #1181 wäre still aus. Pflicht-Gate ist der bestehende
  Mengengleichheits-Test `set(_KEYS) == set(ac["properties"])`; T1-Step 4 führt ihn aus.

## 3. Global Constraints

- **Kein neuer Platzhalter:** `AUTO_COMMIT_BLOCK`/`AUTO_COMMIT_ENABLED` bleiben die einzigen
  (`scripts/lib/consistency/placeholders.py:79, 104`); keine Einträge in
  `scripts/lib/standalone.py:97, 152` ändern.
- **`role_commit_authority()` bleibt unverändert** (`scripts/lib/auto_commit.py:127-143`);
  der Grant lebt ausschließlich in den neuen effektiven Funktionen.
- **Hook-Änderung nur im Grant-Zweig:** `hooks/1-generic/orchestrator-guard-impl.sh` wird
  ausschließlich um das vierte Klassifizierer-Feld (`all_git`), die Vier-Feld-Validierung und das
  Grant-Sentinel-Gate ergänzt (Spec §3.3.1). Der Sentinel-/Mutations-Pfad für `git`,
  `orchestrator` und native `direct`-Rollen bleibt byte-gleich; `# version:` wird
  `1.11.0 → 1.12.0` gebumpt (`hook_drift.py` liest die Zeile).
- **Ein Hook-Prädikat:** Die Guard-Aktivierung wird **nirgends** neu implementiert;
  `hook_state.resolve_hook_enabled` ist die einzige Quelle, `hooks.sync_hooks` und
  `auto_commit` konsumieren sie.
- **Keine Änderung an `config/provider-tools.yaml`** (`opencode_deny_critical`,
  `:58-61`) und **keine** an `config/provider-capabilities.yaml`.
- **Fail-Safe bleibt:** Ungültiger Block ⇒ `mode: off`, `eligible_roles: []`, kein Grant,
  laute Warnung (`scripts/lib/auto_commit.py:269-278`,
  `scripts/lib/sync_pipeline.py:1909-1915`). Neu: das Fail-Safe-Dict trägt zusätzlich
  `authority_overrides: {}`.
- **stdlib only:** `jsonschema` bleibt Test-Abhängigkeit, nie Runtime
  (`scripts/lib/auto_commit.py:167-173`).
- **Byte-Identität als Regressionsanker:** Ohne `authority_overrides` sind gerenderte Agenten,
  `AUTO_COMMIT_BLOCK` und `eligible_roles` byte-identisch zu `aaed14c2`. Einzige Ausnahme ist
  das Allowlist-Artefakt (`version: 2`, K-10) — sie wird als bewusster Default-Diff getestet,
  nicht als Byte-Gleichheit.
- **Ein Commit pro Task**, Englisch, Conventional Commits, ≤ 72 Zeichen, Imperativ, **ohne BOM**
  (Guard-Hook). Kein Push/Tag/Merge — Sache der Rolle `git`.
- **Kein `isolation: "worktree"`**; Arbeit direkt im Projektverzeichnis.
- **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP" -q`
  (nie ein Basetemp im Baum, nie `rtk pytest`).
- **Sprache:** Plan/Doku Deutsch, Code/Tests/Commits Englisch.
- **Serielle Reihenfolge** gegen #1186/#1187/#1188 in Schema, `config.py`, `agent_sync.py`,
  `sync_pipeline.py`, `admin-ui.html` (Spec §9, Matrix §3a): ein PR nach dem anderen, in der
  kanonischen Reihenfolge `#1187 → #1186 → #1188 → #1181 → #1141`.

## 3a. Querschnitt: kanonische Reihenfolge und gemeinsame Konfliktmatrix

**Reihenfolge (verbindlich):** `#1187 → #1186 → #1188 → #1181 → #1141`; die
Whitelist-Ableitung (`PROJECT_WRITABLE_SECTIONS` aus #1186 AC-7) zuletzt. Szenario-IDs:
`94` = #1181, `95–98` = #1187.

| Datei | Issues | Konfliktnatur | Serialisierung |
|---|---|---|---|
| `config/project-config.schema.json` | #1181, #1186, #1187, #1188 | `auto_commit` ist ein `additionalProperties: false`-Block (`:1495-1546`); die anderen ergänzen Top-Level-Sections | seriell |
| `scripts/lib/config.py` | #1181, #1186, #1187, #1188 | `_build_core_variables` (`:1792-1848`) vs. neue Resolver | seriell |
| `scripts/lib/agent_sync.py` | **#1187, #1188, #1181** | **Dieselbe Rollen-Schleife**: #1187 baut `_finalize_agent_content` und den Loop um; #1188 ergänzt dort Provider-/Pane-Aufrufe; #1181 hängt `_apply_role_auto_commit_overrides` (`:92-123`), den Aufruf (`:1457-1468`) und `extra_tools` an `_finalize_agent_content` (`:935`, Transform `:1010`) | seriell, #1181 **nach** #1187/#1188 |
| `scripts/lib/sync_pipeline.py` | **#1186, #1181** (#1187 nur bei echtem Task) | Stage 14 (`:1893-1924`) wird von #1181 und #1186 im selben Block angefasst; #1187 nur, wenn es dort einen echten Task hat | seriell |
| `scripts/lib/variables.py` | **#1187** (nicht #1181) | `conditional_vars` listet `AUTO_COMMIT_ENABLED` (`:572`); #1187 ergänzt dort weitere Variablen in derselben Menge | unabhängig von #1181 |
| `scripts/lib/standalone.py` | **#1187** (nicht #1181) | Platzhalter-Defaults `AUTO_COMMIT_BLOCK` (`:97`) / `AUTO_COMMIT_ENABLED` (`:152`); #1187 ändert Nachbarzeilen | unabhängig von #1181 |
| `hooks/1-generic/orchestrator-guard-impl.sh` | **#1181, #1151** | #1151 härtet denselben Hook; #1181 ergänzt Klassifizierer-Feld + Gate | seriell, **#1151 zuerst** |
| `scripts/lib/hooks.py` + `scripts/lib/hook_state.py` (neu) | #1181 (nur) | `resolve_hook_enabled` wird aus `sync_hooks` herausgezogen | unabhängig |
| `docs/ui/admin-ui.html` | #1181, #1186, #1187, #1188 | `viewProjectAutoCommit` (`:7639-7766`) vs. neue Panes/Router | seriell |
| `tests/scenarios/registry.md` + `tests/scenarios/asserts/*` | **#1181, #1187, #1186** | gemeinsame Nummerierung (`94` vs. `95–98`) | Nummern zuerst abstimmen |
| `templates/configs/project.yaml.example` | **#1187, #1186, #1188, #1181** | `# auto_commit:`-Kommentarblock (`:91`); #1181 dokumentiert `authority_overrides` | seriell |
| `docs/guides/project.yaml.example`, `howto/configs/project.yaml.example` | **#1187, #1186, #1188, #1181** | weitere Beispiel-Kopien ohne `auto_commit`-Block; #1181 ändert sie nicht inhaltlich, prüft sie beim Merge | beim Mergen prüfen |
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CODEBASE_OVERVIEW.md` | alle vier | geteilte Doku-Dateien | seriell (kleine Hunks) |
| `docs/issue-labels.md` | **#1188 erzeugt, #1186 klassifiziert** | Datei entsteht in #1188; Klassifikation in #1186 | nicht #1181 |
| `.meta-config/issue-labels-state.json` | **#1188 erzeugt, #1186 klassifiziert als `unmanaged`** (K1; `project-state` gestrichen) | Negativ-Deklaration der Label-Taxonomie (#1186 `unmanaged[]`), keine Klasse | nicht #1181 |

## 4. File-Structure-Map

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `config/project-config.schema.json` | ändern | `auto_commit.properties.authority_overrides` als Objektform mit Pflicht-Ack (Spec §4.1), `additionalProperties: false` des Blocks bleibt (`:1546`) | T1 |
| `scripts/lib/hook_state.py` | **neu** | `ORCHESTRATOR_GUARD_HOOK`, `ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT`, `resolve_hook_enabled`, `guard_hook_enabled` — ein Prädikat für `hooks.py` und `auto_commit.py` (K-9) | T15 |
| `scripts/lib/hooks.py` | ändern | `sync_hooks` (`:621-626`) nutzt `resolve_hook_enabled`; Warnungstext unverändert | T15 |
| `scripts/lib/auto_commit.py` | ändern | `_KEYS` (`:164`), `ALLOWLIST_VERSION` 1→2 (`:31`), `normalize_authority_overrides`, `authority_override_violations` (+Enforcement), `authority_override_notices`, `effective_commit_authority`, `is_role_eligible`-Erweiterung (`:146-153`), `resolve_auto_commit_config` (`:251-298`), `resolve_commit_grant`, `render_auto_commit_block(..., *, role=None)` (`:322`) | T1, T2, T3, T4, T5, T6 |
| `scripts/lib/config.py` | ändern | `_AUTO_COMMIT_RESOLVED` trägt `authority_overrides` (Fail-Safe + Normalfall, normalisiert) **und** der Fail-Safe prüft `authority_override_violations` (`:1792-1848`, K-13) | T7 |
| `scripts/lib/agent_sync.py` | ändern | `_apply_role_auto_commit_overrides` (Provider-/Guard-Gate, Grant-Logs, Rückgabe `render_bash`) (`:92-123`), `_finalize_agent_content(..., extra_tools=…)` **vor** dem Transform (`:1010`), Aufrufstelle im Rollenloop (`:1457-1468`) | T8 |
| `hooks/1-generic/orchestrator-guard-impl.sh` | ändern | Grant-Zweig (Spec §3.3.1): viertes Klassifizierer-Feld `all_git` (`:1282-1326`), Vier-Feld-Validierung (`:1336`), Grant-Sentinel-Gate neben `:1535`; `# version: 1.11.0 → 1.12.0` | T16 |
| `scripts/lib/provider_transform.py` | **nicht ändern** | Nur Lese-Anker: v1-Permission-Map `:1069-1092`, v2-Builder `:937-972`; Tool-Liste kommt aus dem Content (`:1027`, `:1319-1325`); der tote Gemini-Mapper `:854-870` bleibt unangetastet (F-4) | — |
| `scripts/lib/roles.py` | **nicht ändern** | Präzedenz-Anker `permission-mode-overrides` (`:565-577`) — orthogonal, Doku-Pflicht in T11 | — |
| `scripts/lib/sync_pipeline.py` | ändern | Stage 14 (`:1893-1924`): Schrumpf-Vergleich, Grant-/Skip-Logs, Dry-Run-Vorziehen | T9 |
| `scripts/lib/cli_commands.py` | ändern | semantische Grant-Verstöße in `--validate` (`_handle_validate`, `:1380`, Muster `:1432-1439`) | T2 |
| `.meta-config/auto-commit-allowlist.json` | Laufzeit-Artefakt | neue Form mit `"version": 2` + `"authority_overrides"` (nicht hand-editiert; Stand heute v1, 22 Rollen) | T9 |
| `docs/ui/admin-ui.html` | ändern | Round-Trip-Erhalt unbekannter `auto_commit`-Keys in `viewProjectAutoCommit` (`:7639-7766`, Save `:7753-7762`) | T10 |
| `README.md` | ändern | Auto-commit-Abschnitt (`:477-500`): Grant, Ack-Pflicht, Präzedenz, Shell-Ausweitung, Hook-/Guard-Gate | T11 |
| `docs/api/admin-ui-reference.md` | ändern | Help-Text `auto_commit` (`:181-185`) um `authority_overrides` + YAML-only-Hinweis | T11 |
| `templates/configs/project.yaml.example` | ändern | `# auto_commit:`-Block (`:91`): `authority_overrides` mit `acknowledge_full_shell` als kommentiertes Beispiel | T11 |
| `CHANGELOG.md` | ändern | `Unreleased` (`:3`): Added/Changed/Migration (`version: 2`) | T11 |
| `docs/specs/767-auto-commit-permission-authority.md` | ändern | nur Zeilenanker nachziehen (F-3), keine Inhaltsdebatte | T11 |
| `tests/test_auto_commit_schema.py` | ändern | Schema-Fälle für `authority_overrides` | T1 |
| `tests/test_auto_commit_violations.py` | ändern | Grant-Verstöße (Ack fehlt, read-only, Enforcement) + Notices + `--validate`-rc | T1, T2 |
| `tests/test_auto_commit_authority_grants.py` | **neu** | reine Grant-Funktionen, Provider-/Guard-Gate, Render-Integration (Subprozess-Sync) | T3, T6, T8 |
| `tests/test_auto_commit_lib.py` | ändern | `eligible_roles`/Artefakt-Form/`version: 2`/Normalisierung | T4 |
| `tests/test_auto_commit_block_render.py` | ändern | Grant-Zeile + Byte-Golden `role=None` | T5, T7 |
| `tests/test_auto_commit_allowlist_pipeline.py` | ändern | Schrumpf-Warnung (disjunkte Gründe), Dry-Run, Moduswechsel | T9 |
| `tests/test_orchestrator_guard_hook.py` | ändern | Sentinel akzeptiert `documenter` bei `version: 2` (AC-2) **und** blockt `curl` mit Grant-Sentinel (N-3) | T8, T16 |
| `tests/test_hook_state.py` | **neu** | `resolve_hook_enabled`/`guard_hook_enabled`: Default, `false`, Nicht-Bool | T15 |
| `tests/test_admin_ui_auto_commit_section.py` | **neu** | Text-Pinning des Key-Erhalts (Muster `tests/test_admin_ui_git_section.py`) | T10 |
| `tests/scenarios/configs/94-auto-commit-authority-grant.project.yaml` | **neu** | Szenario auf Basis `18-auto-commit` | T12 |
| `tests/scenarios/asserts/94-auto-commit-authority-grant.sh` | **neu** | Grant gerendert, Nicht-Grant byte-identisch, Allowlist v2 | T12 |
| `tests/scenarios/registry.md` | ändern | Katalogzeile 94 + Pflicht laut `:16-25`, letzte ID heute `93` (`:132`) | T12 |
| `.tmp/scenario-authority-1181/` | Scratch (untracked) | voller End-to-End-Lauf mit `documenter` als Referenzrolle | T13 |

## 5. Meilensteine und Zwischentest-Gates

| M | Inhalt | Tasks | Gate (muss grün sein, bevor M+1 startet) |
|---|---|---|---|
| **M1** | Contract: Hook-Prädikat, Schema-Key + `_KEYS`, Validierung | T1, T15, T2 | `pytest tests/test_hook_state.py tests/test_auto_commit_schema.py tests/test_auto_commit_violations.py` → **0 failed**; `python3 scripts/sync.py --validate` → rc 0; `git diff --name-only aaed14c2..HEAD -- agents/` → leer (commit-fest, K-16) |
| **M2** | Authority-Auflösung (rein): effektive Authority, Allowlist-Form, Render-Text | T3, T4, T5 | `pytest tests/test_auto_commit_lib.py tests/test_auto_commit_block_render.py tests/test_auto_commit_authority_grants.py` → **0 failed**; die bestehenden Byte-Golden-Tests (`test_role_none_is_byte_identical`, `test_default_authority_parameter_stays_direct`) unverändert grün |
| **M3** | Render-Vertrag: Provider- **und** Guard-Gate, Bash-Injektion, Sync-Logs, Variablen | T6, T7, T8 | `pytest tests/test_auto_commit_*.py tests/test_orchestrator_guard_hook.py` → **0 failed**; ein Claude-Sync mit Grant rendert `Bash`; der reale Opencode-Sync rendert `bash: deny` + WARN; positive v1/v2-Permission-Pfade nur gegen den synthetischen Hook-Fixture (K-12); deaktivierter Guard rendert unverändert + WARN bzw. ERROR |
| **M4** | Allowlist-Stage und Hook-Härtung | T9, T16 | `pytest tests/test_auto_commit_allowlist_pipeline.py tests/test_orchestrator_guard_hook.py` → **0 failed**, inkl. exakter WARN-Strings und rc 2 für `curl` mit Grant-Sentinel; `python3 scripts/sync.py --dry-run --check` → rc 0 |
| **M5** | Admin-UI-Round-Trip + Doku | T10, T11 | `pytest tests/test_admin_ui_auto_commit_section.py tests/test_admin_ui_git_section.py` → **0 failed**; Doku-Greps (T11-Step 1) treffen |
| **M6** | End-to-End: Szenario 94 + Scratch-Consumer + Gesamtabnahme | T12, T13, T14 | `tests/scenarios/run.sh 94` → PASS; Scratch-Lauf (T13) belegt alle Punkte aus Step 2–5; volle `tests/test_auto_commit_*.py`-Suite → **0 failed** (Bestand 75, siehe §8); `--validate` rc 0, `--check` rc 0 |

**Regel:** Kein Task beginnt, bevor das Gate seines Meilensteins grün ist. Ein rotes Gate wird
nicht „durchgewunken" — der Task bleibt offen (Plan-Ledger-Konvention).

---

## 6. Bite-sized TDD-Tasks

### T1 — Schema-Key `authority_overrides` + `_KEYS` (M1, S)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `config/project-config.schema.json` (`auto_commit.properties`, `:1498-1545`)
- Modify: `scripts/lib/auto_commit.py` (`_KEYS`, `:164`; `ALLOWLIST_VERSION`, `:31`)
- Modify: `tests/test_auto_commit_schema.py`
- Modify: `tests/test_auto_commit_violations.py`

**Interfaces:** Produces den Schema-Teilblock `auto_commit.properties.authority_overrides`
(Object; `propertyNames.pattern ^[a-z0-9][a-z0-9-]*$`; `additionalProperties` = Objekt mit
`required ["authority", "acknowledge_full_shell"]`, `authority.const "direct"`,
`acknowledge_full_shell.const true`, `additionalProperties false`; `default {}`);
Consumes nichts.

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_schema.py` (Muster `_base_config`,
  `jsonschema.validate` wie `:21-30`):
  `test_authority_overrides_direct_with_ack_is_valid`
  (`{"mode": "auto", "triggers": ["task-boundary"], "authority_overrides":
  {"documenter": {"authority": "direct", "acknowledge_full_shell": true}}}` validiert fehlerfrei),
  `test_authority_overrides_scalar_shorthand_rejected` (`{"documenter": "direct"}` ⇒
  `ValidationError`, K-8),
  `test_authority_overrides_missing_ack_rejected` (`{"documenter": {"authority": "direct"}}` ⇒
  `ValidationError`),
  `test_authority_overrides_ack_must_be_true` (`{"acknowledge_full_shell": false}` ⇒
  `ValidationError`),
  `test_authority_overrides_rejects_unknown_value` (`{"authority": "notify"}` ⇒ `ValidationError`),
  `test_authority_overrides_rejects_unknown_subkey` (`{"authority": "direct",
  "acknowledge_full_shell": true, "extra": 1}` ⇒ `ValidationError`),
  `test_authority_overrides_rejects_bad_role_name` (`{"Documenter": {…}}` und `{"_x": {…}}` ⇒
  `ValidationError`), `test_authority_overrides_default_is_empty_object` (Schema-`default` ist `{}`,
  nicht `null`). In `tests/test_auto_commit_violations.py`:
  `test_authority_overrides_key_is_known` (`auto_commit_violations({... "authority_overrides":
  {"documenter": {"authority": "direct", "acknowledge_full_shell": true}}}) == []`).
  Lauf → **rot — 8 + 1 failed** (`ValidationError` bleibt aus, `unknown key(s)` erscheint).
- [ ] Step 2: Schema-Block einfügen — exakt nach Spec §4.1, `description` wörtlich übernehmen;
  Position im Objekt ist irrelevant (`"custom_script"` `:1532`, `"file_count_threshold"` `:1526`).
- [ ] Step 3: `_KEYS` (`:164`) um `"authority_overrides"` ergänzen; `ALLOWLIST_VERSION = 2`
  (`:31`). **Schema und `_KEYS` ändern sich im selben PR** (K8/K-19) — kein Zwischenstand mit
  Schema-Key ohne `_KEYS`-Eintrag, sonst deaktiviert der Fail-Safe die ganze Authority. Der
  bestehende Mengengleichheits-Test `test_enum_constants_match_schema`
  (`tests/test_auto_commit_violations.py:111-123`, `assert set(_KEYS) ==
  set(schema["properties"]["auto_commit"]["properties"])`) ist damit der Wächter gegen F-1 und
  gegen die K8-Drift.
- [ ] Step 4: Verifikation:
  `python3 -m pytest tests/test_auto_commit_schema.py tests/test_auto_commit_violations.py
  --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** (Bestand 30 = 12 Schema + 18 Violations, siehe
  §8; 9 neu); `python3 scripts/sync.py --validate` → **rc 0**;
  `python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.auto_commit import ALLOWLIST_VERSION; print(ALLOWLIST_VERSION)"` → `2`.
- [ ] Step 5: Commit `feat: add opt-in commit authority override to the config schema`.

### T2 — `authority_override_violations` + Notices + `--validate`-Wiring (M1, L)

**Agent:** senior-developer
**Depends on:** T1, T15
**Files:**
- Modify: `scripts/lib/auto_commit.py`
- Modify: `scripts/lib/cli_commands.py` (`_handle_validate`, `:1380`; Muster `:1432-1439`)
- Modify: `tests/test_auto_commit_violations.py`

**Interfaces:** Produces
`authority_override_violations(config: dict, agent_meta_root: Path,
provider_config: Mapping | None = None) -> list[str]` (jede Meldung beginnt mit
`auto_commit.authority_overrides.`, Meldungstexte exakt nach Spec §4.3) und
`authority_override_notices(config: dict, active_roles: Iterable[str]) -> list[str]`;
Consumes `normalize_authority_overrides` (T1/T4), `role_commit_authority` (`:127-143`),
`AUTHORITY_NONE` (`:37`), `guard_hook_enabled` (T15), `provider_hooks_supported`
(`scripts/lib/providers.py:700-709`), `resolve_providers`
(`scripts/lib/providers.py:498-578`), in `--validate` den Zähler `consistency_errors`
(`cli_commands.py:1396`) und die bereits geladene `_provider_config` (`:1462`).
`active_roles` in `authority_override_notices` ist die **effektive** aktive Menge
(`raw_roles ∩ active_set.has`, K-15/RVW2-1181-05).

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_violations.py` (Grant-Helper
  `_grant(role)` liefert `{role: {"authority": "direct", "acknowledge_full_shell": True}}`):
  `test_authority_override_valid_grant_has_no_violation` (`_grant("documenter")` + `_REPO_ROOT` ⇒
  `[]`), `test_authority_override_missing_ack_rejected`
  (`{"documenter": {"authority": "direct"}}` ⇒ Meldung nennt `acknowledge_full_shell`),
  `test_authority_override_scalar_value_rejected` (`{"documenter": "direct"}` ⇒ Meldung,
  kein `TypeError`, K-8), `test_authority_override_unknown_value_rejected`
  (`{"authority": "notify"}` ⇒ Meldung mit `authority_overrides.documenter`),
  `test_authority_override_read_only_role_rejected` (`_grant("explorer")` ⇒ Meldung nennt
  `no Edit/Write`), `test_authority_override_typo_role_rejected`
  (`_grant("documenterr")` ⇒ Meldung, **weil** abgeleitete Authority `none`),
  `test_authority_override_non_mapping_rejected` (`{"authority_overrides": ["documenter"]}` ⇒
  Meldung, kein `TypeError`),
  `test_grant_not_enforced_when_guard_disabled` (`hooks: {orchestrator-guard: {enabled: false}}` +
  `_grant("documenter")` ⇒ Meldung `grant not enforced (guard hook disabled:
  hooks.orchestrator-guard.enabled is not true)`),
  `test_grant_not_enforced_on_hookless_provider` (`ai-providers: [Opencode]` + Grant +
  `provider_config`-Fixture mit `has_hooks: false` ⇒ Meldung `grant not enforced (provider
  'Opencode', reason has_hooks=false)`),
  `test_grant_enforced_on_mixed_provider_set_is_no_violation` (`ai-providers: [Claude, Opencode]`
  ⇒ `[]`, WARN bleibt dem Sync überlassen — Spec §4.3),
  `test_authority_override_inactive_role_is_not_a_violation`
  (`_grant("documenter")` + `active_roles=["developer"]` ⇒ `[]` für die Violations **und**
  `authority_override_notices(...)` liefert genau eine INFO-Zeile `grant ignored — role is not
  active`),
  `test_grant_notice_for_gate_dropped_role` (Rolle steht in `roles:`/`raw_roles`, ist aber
  `active_set.has(role) == False` ⇒ ebenfalls genau eine INFO-Zeile; K-15/RVW2-1181-05),
  plus zwei Subprozess-Tests
  `test_validate_rc1_on_read_only_grant` (`sync.py --validate` mit `explorer`-Grant ⇒ rc 1,
  `config-audit [ERROR] auto_commit: auto_commit.authority_overrides.explorer` in der Ausgabe) und
  `test_validate_rc1_on_grant_without_active_guard` (Claude + `orchestrator-guard.enabled: false`
  ⇒ rc 1, N-1).
  Lauf → **rot — 14 failed**.
- [ ] Step 2: `normalize_authority_overrides(raw)` implementieren (eine Normalisierung, K-8):
  `{role: "direct"}` nur für Objekte mit `authority == "direct"` **und**
  `acknowledge_full_shell is True`; alles andere wird übergangen (die Violation kommt aus Step 3).
- [ ] Step 3: `authority_override_violations` implementieren — **reihenfolge-stabil**, sortiert
  nach Rollenname: (a) `authority_overrides` ist kein Mapping ⇒ eine Meldung, (b) je Rolle:
  Muster `^[a-z0-9][a-z0-9-]*$`; Form/Ack/`authority` (Meldungen exakt Spec §4.3); abgeleitete
  Authority `== AUTHORITY_NONE`; (c) **einmal** je gegranteter Rolle (nicht je Provider) die
  Enforcement-Meldung, wenn `guard_hook_enabled(config)[0]` False ist **oder** kein aktiver
  Provider `provider_hooks_supported(...)` erfüllt. Provider-Namen sortiert, bei einem
  Provider `provider 'X'`, bei mehreren `providers 'A', 'B'` (Spec §4.3).
  `provider_config=None` ⇒ `load_providers_config(agent_meta_root, config)`. **Nur wenn** die
  normalisierte Grant-Map nicht leer ist — im dominanten Fall „kein Grant" wird die
  Provider-Registry gar nicht geladen (Performance, gleiche Semantik).
- [ ] Step 4: `authority_override_notices(config, active_roles)` implementieren: je Grant, dessen
  Rolle nicht in `active_roles` steht, eine INFO-Zeile (Spec §4.3). Der Parameter `active_roles`
  lebt damit ausschließlich hier (K-2).
- [ ] Step 5: `auto_commit_violations` **nicht** erweitern (sie bleibt rein strukturell);
  `resolve_auto_commit_config` ruft in T4 **beide** Prüfungen (Spec §4.3).
- [ ] Step 6: In `_handle_validate` **nach** `_provider_config = _load_pc(agent_meta_root)`
  (`cli_commands.py:1462`) einfügen — die bestehende `auto_commit_violations`-Schleife
  (`:1432-1439`) bleibt unverändert:
  `for _grant_violation in authority_override_violations(config, agent_meta_root, _provider_config):`
  → `log.warning(f"config-audit [ERROR] auto_commit: {_grant_violation}")`,
  `consistency_errors += 1`; danach
  `for _grant_notice in authority_override_notices(config,
  {r for r in (ctx.active_set.raw_roles or ()) if ctx.active_set.has(r)}):`
  → `log.note(f"config-audit [INFO] auto_commit: {_grant_notice}")` **ohne** Zählererhöhung.
  Die effektive Menge ist Pflicht (K-15/RVW2-1181-05), sonst erhält eine gate-dropped Rolle
  keine Notice.
  Kein Exit an dieser Stelle (bestehender Mechanismus).
- [ ] Step 7: Verifikation: obige Tests **grün — 14 passed**;
  `python3 -m pytest tests/test_auto_commit_violations.py --basetemp="$PYTEST_BASETEMP" -q`
  → **0 failed**; `python3 scripts/sync.py --validate` → rc 0 (Selbst-Hosting hat keinen Grant).
- [ ] Step 8: Commit `feat: reject invalid or unenforced commit authority grants in validation`.

### T3 — `effective_commit_authority` + `is_role_eligible`-Erweiterung (M2, M)

**Agent:** developer
**Depends on:** T1
**Files:**
- Modify: `scripts/lib/auto_commit.py`
- Create: `tests/test_auto_commit_authority_grants.py`

**Interfaces:** Produces
`effective_commit_authority(role, agent_meta_root, platform=None, authority_overrides=None) -> str`
(eskaliert `delegate|notify` → `direct` nur bei `wanted == "direct"`, wirft nie; ein
Nicht-Mapping wird wie „kein Grant" behandelt, K-14) und
`is_role_eligible(role, agent_meta_root, platform=None, authority_overrides=None) -> bool`
(`== AUTHORITY_DIRECT` der effektiven Funktion, Default `None` = altes Verhalten).
**Beide Parameter erwarten die normalisierte Map** `{role: "direct"}` (T2/K-8), nicht die
Config-Objektform; die Normalisierung passiert genau einmal in `resolve_auto_commit_config` (T4)
und in `resolve_commit_grant` (T6).
Consumes `role_commit_authority` (`:127-143`), `AUTHORITY_*` (`:34-37`).

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_authority_grants.py` (Moduldocstring
  nennt Spec §3.2 + AC-1): `test_notify_role_escalates_to_direct`
  (`effective_commit_authority("documenter", _REPO_ROOT, None, {"documenter": "direct"}) == "direct"`),
  `test_delegate_role_escalates_to_direct` (`orchestrator`), `test_no_override_is_identity`
  (Parametrisierung über **alle** 98 deploybaren Templates: Ergebnis ==
  `role_commit_authority(...)`; Liste zur Laufzeit aus `agents/1-generic/*.md` minus
  `_README.md`/`_reference-agent.md`/`_wf-orchestrator-reference.md`),
  `test_derived_direct_is_noop` (`developer` mit Grant ⇒ `direct`, kein Fehler),
  `test_read_only_role_never_escalates` (`explorer` + Grant ⇒ `none`),
  `test_override_for_other_role_does_not_leak` (`{"planner": "direct"}` + `documenter` ⇒ `notify`),
  `test_non_mapping_or_unknown_value_never_raises` (`authority_overrides=["x"]`,
  `{"documenter": "notify"}`, `{}` ⇒ jeweils keine Exception, abgeleiteter Wert),
  `test_is_role_eligible_matches_effective_authority` (Kreuzprodukt über 5 Rollen × Grant an/aus).
  Lauf → **rot — 8 failed** (`ImportError: cannot import name 'effective_commit_authority'`).
- [ ] Step 2: `effective_commit_authority` implementieren — reine Funktion, keine I/O außer
  `_role_tools`-Lesen; Reihenfolge exakt Spec §3.2 Nr. 1–5. Der Override-Zugriff lautet
  `authority_overrides.get(role) if isinstance(authority_overrides, Mapping) else None`
  (K-14/RVW2-1181-04), damit `authority_overrides=["x"]` keinen `AttributeError` auslöst.
- [ ] Step 3: `is_role_eligible` delegieren (`return effective_commit_authority(...) == AUTHORITY_DIRECT`),
  Docstring ergänzen: „ein Grant ist die **einzige** Ausnahme vom direct-only-Prinzip und wird
  von `authority_override_violations` auf schreibfähige Rollen begrenzt".
- [ ] Step 4: Verifikation: **grün — 8 passed**; Regression
  `python3 -m pytest tests/test_auto_commit_lib.py --basetemp="$PYTEST_BASETEMP" -q` → 0 failed
  (bestehende `is_role_eligible`-Aufrufe ohne `authority_overrides` unverändert).
- [ ] Step 5: Commit `feat: resolve an effective commit authority with an opt-in grant`.

### T4 — `resolve_auto_commit_config` trägt den Grant ins Artefakt (M2, M)

**Agent:** developer
**Depends on:** T3
**Files:**
- Modify: `scripts/lib/auto_commit.py` (`:251-298`)
- Modify: `tests/test_auto_commit_lib.py`

**Interfaces:** Produces `resolve_auto_commit_config(...)-> dict` mit den zusätzlichen
Schlüsseln `authority_overrides` (normalisierte Map, nur Rollen aus `active_roles`) und
`version: 2`; Consumes `authority_override_violations` (T2), `normalize_authority_overrides` (T2),
`is_role_eligible(..., authority_overrides=…)` (T3), `ALLOWLIST_VERSION` (T1).

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_lib.py`:
  `test_granted_notify_role_becomes_eligible` (`roles=["documenter","developer"]`,
  `authority_overrides={"documenter": {"authority": "direct", "acknowledge_full_shell": True}}` ⇒
  `eligible_roles == ["developer","documenter"]`),
  `test_grant_is_mode_independent` (gleiches Ergebnis unter `mode: off` und `mode: suggest`),
  `test_artifact_carries_only_active_grants` (`documenter` + `planner` gegrantet, `active_roles`
  nur `["documenter"]` ⇒ `authority_overrides == {"documenter": "direct"}` — normalisierte Map),
  `test_artifact_version_is_two` (`out["version"] == 2`),
  `test_grant_without_roles_key_has_no_effect` (`active_roles=[]` ⇒ `eligible_roles == []`),
  `test_grant_without_ack_triggers_fail_safe` (`{"documenter": {"authority": "direct"}}` ⇒
  `mode == "off"`, `eligible_roles == []`, `authority_overrides == {}`),
  `test_invalid_grant_triggers_fail_safe` (`_grant("explorer")` ⇒
  `mode == "off"`, `eligible_roles == []`, `authority_overrides == {}`),
  `test_fail_safe_artifact_shape_includes_grant_map` (`authority_overrides`-Key vorhanden,
  Wert `{}`).
  Lauf → **rot — 8 failed**.
- [ ] Step 2: Fail-Safe-Zweig (`:269-278`): `"authority_overrides": {}` + `version:
  ALLOWLIST_VERSION` (schon da) ergänzen; Bedingung auf
  `if auto_commit_violations(config) or authority_override_violations(config, agent_meta_root):`.
- [ ] Step 3: Normalfall: `overrides = {r: v for r, v in normalize_authority_overrides(
  ac_cfg.get("authority_overrides")).items() if r in set(active_roles)}`
  und `eligible_roles` über `is_role_eligible(..., authority_overrides=overrides)`; Rückgabe um
  `"authority_overrides": overrides` ergänzen. **Keine** Änderung an `mode`/`triggers`-Semantik.
- [ ] Step 4: Verifikation: **grün — 8 passed**; `tests/test_auto_commit_violations.py` bleibt grün.
- [ ] Step 5: Commit `feat: record granted roles in the auto-commit allowlist`.

### T5 — Grant-Zeile im `AUTO_COMMIT_BLOCK` + Byte-Golden (M2, M)

**Agent:** developer
**Depends on:** T4
**Files:**
- Modify: `scripts/lib/auto_commit.py` (`render_auto_commit_block`, `:322`)
- Modify: `tests/test_auto_commit_block_render.py`

**Interfaces:** Produces
`render_auto_commit_block(resolved: dict, authority: str = AUTHORITY_DIRECT, *, role: str | None = None) -> str`;
Consumes `resolved["authority_overrides"]` (T4) und die bestehenden Textbausteine
(`:39-54`, `:378-458`).

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_block_render.py`:
  `test_granted_role_gets_grant_line` (`auto`-Resolved mit
  `authority_overrides={"documenter":"direct"}`, `role="documenter"` ⇒ Block enthält wörtlich
  ``Granted by project config `auto_commit.authority_overrides.documenter` (issue #1181).``
  **und** `full `Bash` grant, not a `git`-only grant` **und** die `add`/`commit`-Grenze),
  `test_non_granted_role_has_no_grant_line`
  (gleiches `resolved`, `role="planner"` ⇒ kein `#1181`), `test_role_none_is_byte_identical`
  (für alle 6 Kombinationen `mode ∈ {off, suggest, auto(direct/delegate/notify)}` gilt
  `render_auto_commit_block(r) == render_auto_commit_block(r, role=None)` und beide == der
  heutigen Ausgabe; Vergleich gegen eingebettete Erwartungstexte, keine Datei-Golden),
  `test_grant_line_only_in_direct_authority` (`authority="notify"`, `role="documenter"` ⇒ keine
  Grant-Zeile, weil sie den Render-Vertrag sonst lügen würde),
  `test_grant_line_does_not_mention_push_tag_branch` (bestehende Invariante `:17` bleibt).
  Lauf → **rot — 5 failed**.
- [ ] Step 2: Neue Konstante `_GRANT_LINE_TEMPLATE` neben `_BOM_LINE` (`:45-49`), Wortlaut exakt
  nach Spec §4.5; im `AUTHORITY_DIRECT`-Zweig von `auto` (`:429-435`) und `custom` (`:399-406`)
  nach der Sentinel-Zeile einfügen, wenn
  `role and resolved.get("authority_overrides", {}).get(role) == "direct"`.
  `_BOM_LINE`/`_PUSH_BOUNDARY_LINE` bleiben **letzte** zwei Zeilen (Reihenfolge unverändert).
- [ ] Step 3: Rückwärtskompatibilität belegen: `role=None` ⇒ kein zusätzlicher Zweig, gleiche
  Zeilenzahl; die 20 bestehenden Tests dieser Datei bleiben unverändert.
- [ ] Step 4: Verifikation: **grün — 5 passed**, `python3 -m pytest
  tests/test_auto_commit_block_render.py tests/test_auto_commit_coverage.py --basetemp="$PYTEST_BASETEMP" -q`
  → 0 failed.
- [ ] Step 5: Commit `feat: state the granted authority in the rendered commit block`.

### T6 — `resolve_commit_grant` inkl. Provider-/Guard-Gate (M3, M)

**Agent:** developer
**Depends on:** T3, T15
**Files:**
- Modify: `scripts/lib/auto_commit.py`
- Modify: `tests/test_auto_commit_authority_grants.py`

**Interfaces:** Produces
`resolve_commit_grant(role: str, resolved: dict, provider_capabilities: dict | None,
agent_meta_root: Path, *, guard_enabled: bool) -> tuple[str, bool]`
→ `(authority, render_bash)`; Consumes `provider_hooks_supported(pc)`
(`scripts/lib/providers.py:700-709`), `guard_hook_enabled` (T15), `effective_commit_authority`
(T3), `AUTHORITY_DIRECT`.

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_authority_grants.py` (Aufrufe immer mit
  `agent_meta_root=_REPO_ROOT, guard_enabled=True`):
  `test_grant_on_hook_provider_renders_bash` (`{"has_hooks": True, "hook_protocol":
  "claude-code-json"}` + `mode: auto` + Grant ⇒ `("direct", True)`),
  `test_grant_on_antigravity_provider_renders_bash` (`antigravity-hooks-json` ⇒ `True`),
  `test_grant_on_hookless_provider_does_not_render` (`{"has_hooks": False}` ⇒
  `("notify", False)` für `documenter`),
  `test_grant_on_provider_without_verified_protocol_does_not_render`
  (`{"has_hooks": True, "hook_protocol": None}` — Form von Mammouth
  `config/ai-providers.yaml:622` und Codex `:734` ⇒ `(derived, False)`),
  `test_grant_under_off_and_suggest_does_not_render` (`mode: off`/`suggest` ⇒ `(derived, False)`),
  `test_grant_without_active_guard_does_not_render`
  (`guard_enabled=False` + Hook-Provider ⇒ `("notify", False)`, RVW-1181-01),
  `test_derived_direct_role_never_needs_bash_injection` (`developer` ⇒ `("direct", False)`, K-3),
  `test_none_capabilities_fail_closed` (`provider_capabilities=None` ⇒ `(derived, False)`,
  keine Exception). Lauf → **rot — 8 failed**.
- [ ] Step 2: Implementieren:
  `authority = effective_commit_authority(role, agent_meta_root, None, resolved.get("authority_overrides"))`;
  `granted = resolved.get("authority_overrides", {}).get(role) == "direct"`;
  `render_bash = granted and resolved.get("mode") in ("auto", "custom") and guard_enabled and provider_hooks_supported(pc or {}) and "Bash" not in _role_tools(role, agent_meta_root)`.
- [ ] Step 3: Docstring: beide Gate-Begründungen — ohne Hook wäre `direct`-Prosa auf `bash: deny`
  der #767-Widerspruch; ohne aktiven Guard wäre `Bash` eine unbeschränkte Shell (Spec §3.3) —
  plus Verweis `#1181`/`#1151`.
- [ ] Step 4: Verifikation: **grün — 8 passed**; `python3 -m pytest
  tests/test_auto_commit_authority_grants.py --basetemp="$PYTEST_BASETEMP" -q` → 0 failed.
- [ ] Step 5: Commit `feat: gate the rendered grant on a provider hook and an active guard`.

### T7 — `_AUTO_COMMIT_RESOLVED` trägt `authority_overrides` (M3, S)

**Agent:** developer
**Depends on:** T2, T4
**Files:**
- Modify: `scripts/lib/config.py` (`_build_core_variables`, `:1792-1848`)
- Modify: `tests/test_auto_commit_block_render.py`

**Interfaces:** Produces `variables["_AUTO_COMMIT_RESOLVED"]["authority_overrides"]`
(`dict[str, str]`, normalisiert, Fail-Safe `{}`); Consumes `_auto_commit_cfg` (`:1805`),
`normalize_authority_overrides` (T2) und `authority_override_violations` (T2) —
der Fail-Safe-Zweig prüft **beide** Verstoßklassen (K-13/RVW2-1181-03).

- [ ] Step 1: **Test zuerst**: `test_core_variables_carry_authority_overrides`
  (`build_variables(cfg, ...)` mit `auto_commit.authority_overrides: {documenter: {authority:
  direct, acknowledge_full_shell: true}}` ⇒
  `variables["_AUTO_COMMIT_RESOLVED"]["authority_overrides"] == {"documenter": "direct"}`),
  `test_core_variables_grant_without_ack_triggers_fail_safe` (Objekt ohne Ack ⇒
  `_AUTO_COMMIT_RESOLVED["mode"] == "off"`, `authority_overrides == {}` **und**
  `INVALID_CONFIG_MARKER` gesetzt — der Test, der ohne den `authority_override_violations`-Aufruf
  rot bleibt, RVW2-1181-03),
  `test_core_variables_invalid_block_has_empty_grant_map` (Block mit `triggers` unter `mode: off`
  ⇒ `{}` + `INVALID_CONFIG_MARKER` weiterhin gesetzt),
  `test_core_variables_without_block_have_empty_grant_map` (`auto_commit` fehlt ⇒ `{}`,
  `AUTO_COMMIT_ENABLED == "false"`). Lauf → **rot — 4 failed** (`KeyError` bzw. fehlender
  Fail-Safe).
- [ ] Step 2: Im Fail-Safe-Zweig (`:1806`, `:1814-1821`) `"authority_overrides": {}` ergänzen und
  die Bedingung auf
  `if auto_commit_violations(config) or authority_override_violations(config, agent_meta_root):`
  erweitern (K-13). Im Normalfall (`:1827-1833`)
  `"authority_overrides": normalize_authority_overrides(_auto_commit_cfg.get("authority_overrides"))`.
  **Nicht** gegen `roles:` filtern — das ist Sache von T8/T9; `config.py` kennt hier nur den Block.
- [ ] Step 3: Verifikation: **grün — 4 passed**; `python3 scripts/sync.py --dry-run` → rc 0 und
  kein `KeyError` in `sync.log`.
- [ ] Step 4: Commit `feat: expose the authority overrides to the per-role render`.

### T8 — Provider-Gate + `Bash`-Injektion **vor** dem Transform + Sync-Logs (M3, L)

**Agent:** senior-developer
**Depends on:** T6, T7
**Files:**
- Modify: `scripts/lib/agent_sync.py`
- Modify: `tests/test_auto_commit_authority_grants.py`
- Modify: `tests/test_orchestrator_guard_hook.py`

**Interfaces:** Produces
`_apply_role_auto_commit_overrides(merged_vars, role, agent_meta_root, variables, *, config=None, provider=None, provider_capabilities=None, log=None, guard_off_logged=None) -> bool`
(Rückgabe `render_bash`; `guard_off_logged: set[str] | None` dedupliziert die Guard-aus-WARN je
Rolle über alle Provider hinweg) und
`_finalize_agent_content(..., *, extra_tools: list[str] | None = None)`; Consumes
`resolve_commit_grant` (T6), `guard_hook_enabled` (T15),
`append_frontmatter_tools` (`scripts/lib/frontmatter.py:184-209`),
`provider_hooks_supported` (`scripts/lib/providers.py:700-709`).

- [ ] Step 1: **Test zuerst** (Subprozess-Sync, Muster
  `tests/test_auto_commit_allowlist_pipeline.py:13-43`) in
  `tests/test_auto_commit_authority_grants.py` (Grant-Helper `_grant_yaml(role)` erzeugt
  `authority: direct` + `acknowledge_full_shell: true`):
  `test_claude_documenter_gains_bash_when_granted` (Projekt mit
  `roles: [orchestrator, developer, documenter]`, `ai-providers: [Claude]`,
  `auto_commit: {mode: auto, triggers: [task-boundary], authority_overrides: {documenter: {authority: direct, acknowledge_full_shell: true}}}`
  ⇒ `.claude/agents/documenter.md` enthält im Frontmatter `- Bash` **und** die Grant-Zeile im
  Body), `test_claude_documenter_without_grant_keeps_bash_deny` (dito ohne Key ⇒ **kein**
  `Bash`, Block ohne `#1181`), `test_claude_grant_with_disabled_guard_keeps_bash_deny`
  (`hooks: {orchestrator-guard: {enabled: false}}` ⇒ kein `Bash`, `sync.log` enthält
  `auto-commit-grant: documenter=direct not enforced (guard hook disabled:
  hooks.orchestrator-guard.enabled is not true); rendered as notify (issue #1181)`, N-1),
  `test_opencode_v1_documenter_bash_deny_by_default`
  (`bash: deny`; der einzige reale Opencode-Renderfall, K-12),
  `test_render_bash_on_synthetic_hook_capable_fixture` (Unit-Ebene auf
  `_apply_role_auto_commit_overrides`: `provider_capabilities={"has_hooks": True,
  "hook_protocol": "claude-code-json"}` + Grant ⇒ `render_bash is True` und Block enthält die
  Grant-Zeile; ersetzt die mit Opencode unerreichbaren v1/v2-Allow-Tests, K-12),
  `test_hookless_provider_renders_derived_and_warns` (Opencode ⇒ `bash: deny`, Block enthält
  `notify`-Prosa und **keine** Grant-Zeile, `sync.log` enthält
  `auto-commit-grant: documenter=direct not enforced on provider 'Opencode' (has_hooks=false); rendered as notify (issue #1181)`),
  `test_grant_log_line_on_claude` (`auto-commit-grant: documenter=direct (source: auto_commit.authority_overrides; hook-enforced: yes)`),
  `test_grant_on_inactive_role_is_logged_as_info` (`roles: [developer]` + Grant auf `planner` ⇒
  INFO-Zeile `grant ignored — role is not active`), `test_gemini_grant_maps_to_run_command`
  (K-4: `.gemini/agents/documenter.md` enthält `run_command`, **nicht** `code_execution`),
  `test_ungranted_roles_render_byte_identical`
  (zwei Syncs — mit/ohne Key — in zwei Temp-Verzeichnissen; `diff -r` über alle generierten
  `.md` außer `documenter.md` und `sync.log` ist leer).
  In `tests/test_orchestrator_guard_hook.py`:
  `test_allowlist_sentinel_accepts_documenter_with_v2_allowlist`
  (Allowlist-Helper `_write_allowlist` (`:949-958`) um `authority_overrides=None` erweitert, hier
  auf `version: 2` + `eligible_roles: ["documenter"]` +
  `authority_overrides: {"documenter": "direct"}`;
  `#agent-meta:agent=documenter\ngit add -A && git commit -m 'x'` ⇒ rc 0) und
  `test_v2_allowlist_still_blocks_push_for_granted_role`
  (`... git push origin main` ⇒ rc 2; AC-2-Grenze).
  Lauf → **rot — 12 failed**.
- [ ] Step 2: `_apply_role_auto_commit_overrides`: Signatur additiv erweitern (`config`,
  `guard_off_logged`); nach der bestehenden `off`-Behandlung (`:117-120`)
  `guard_on, _guard_invalid = guard_hook_enabled(config or {})` und
  `authority, render_bash = resolve_commit_grant(role, resolved, provider_capabilities,
  agent_meta_root, guard_enabled=guard_on)`; `merged_vars["AUTO_COMMIT_BLOCK"] =
  render_auto_commit_block(resolved, authority, role=role)`; Logs bei `log`:
  INFO-Zeile bei `granted and render_bash`, WARN-Zeile bei `granted and not render_bash`
  (Unterscheidung Guard-aus vs. Provider ohne Hook, Formate Spec §4.6 wörtlich). Die
  Guard-aus-WARN wird über `guard_off_logged` je Rolle nur **einmal** emittiert, auch wenn
  mehrere Provider synchronisiert werden. `return render_bash`.
- [ ] Step 3: Aufrufstelle `sync_agents_for_provider` (`:1459`): vor der Rollen-Schleife
  `guard_off_logged: set[str] = set()` anlegen und
  `render_bash = _apply_role_auto_commit_overrides(merged_vars, role, agent_meta_root, variables,
  config=config, provider=provider, provider_capabilities=pc, log=log,
  guard_off_logged=guard_off_logged)` — `pc` stammt aus
  `_resolve_sync_targets` (`:1423`), der bereits `has_hooks`/`hook_protocol` trägt.
- [ ] Step 4: `_finalize_agent_content`: neuen keyword-only Parameter `extra_tools` und direkt
  **vor** `transform_agent_content_for_provider` (`:1010`):
  `if extra_tools: content = append_frontmatter_tools(content, extra_tools)`.
  `sync_agents_for_provider` übergibt `extra_tools=["Bash"] if render_bash else None`.
  **Nicht** die MCP-Injektion (`:1027-1040`) als Ort nutzen — sie läuft bewusst nach dem
  Transform und würde bei Opencode die Permission-Map nicht mehr erreichen
  (`provider_transform.py:1069-1092` liest den Content).
- [ ] Step 5: Verifikation: **grün — 12 passed**; Regression
  `python3 -m pytest tests/test_auto_commit_block_render.py tests/test_auto_commit_coverage.py
  tests/test_auto_commit_developer_reference.py tests/test_mcp_role_overrides.py --basetemp="$PYTEST_BASETEMP" -q`
  → 0 failed; `python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 6: Commit `feat: render a granted commit authority with provider enforcement`.

### T9 — Allowlist-Stage: `version: 2`, Schrumpf-Warnung, Dry-Run (M4, L)

**Agent:** senior-developer
**Depends on:** T4
**Files:**
- Modify: `scripts/lib/sync_pipeline.py` (`:1893-1924`)
- Modify: `tests/test_auto_commit_allowlist_pipeline.py`

**Interfaces:** Produces `_sync_stage_auto_commit_allowlist` mit read-only Vorwärtsvergleich
vor dem Schreibpfad; privater Helfer
`_previous_allowlist(project_root: Path) -> dict | None` und
`_shrink_reasons(previous: dict, resolved: dict, roles_cfg, active_set, agent_meta_root) -> list[tuple[str, str]]`
(disjunkte Gründe, K-5); Consumes `json`, `write_atomic`, `effective_commit_authority` (T3),
`resolve_auto_commit_config` (T4).

- [ ] Step 1: **Test zuerst** in `tests/test_auto_commit_allowlist_pipeline.py`:
  `test_shrink_warning_lists_dropped_roles_with_reasons` (vorherige Allowlist mit
  `eligible_roles` aus 24 Namen inkl. `copyeditor`, `documenter`, `product-manager`, `planner`;
  Sync mit `roles: [developer, tester, git, copyeditor, documenter, planner]` — d. h.
  `product-manager` **fehlt** jetzt ⇒ WARN-Zeile beginnt mit
  `auto-commit-allowlist: eligible_roles shrank 24 -> `, enthält `(-`, `copyeditor (no Bash)`,
  `documenter (no Bash)`, `planner (no Bash)`, `product-manager (role removed)` und endet bei
  > 20 Rollen auf `… (+N more)`),
  `test_no_bash_reason_requires_role_in_roles` (Rolle nicht in `roles:` und nie gegrantet ⇒
  `(role removed)`, **nie** `(no Bash)`; deckt RVW-1181-04 ab),
  `test_shrink_warning_reports_gate_dropped` (Fixture `tests/fixtures/active-set/p20` wie
  `:72-80`; Rolle steht in `roles:` ⇒ `(gate-dropped)`),
  `test_shrink_warning_reports_withdrawn_grant` (vorherige v2-Datei mit
  `authority_overrides: {documenter: direct}` + `eligible_roles` mit `documenter`, aktueller
  Lauf ohne Grant **und** `documenter` weiterhin in `roles:` ⇒ `documenter (grant withdrawn)`,
  nicht `no Bash`),
  `test_mode_change_to_off_is_reported` (vorher `mode: auto`, aktuell `mode: off` ⇒ exakt
  `auto-commit-allowlist: mode changed auto -> off; all <n> eligible role(s) dropped`),
  `test_missing_previous_allowlist_is_info` (Erst-Sync ⇒ INFO-Zeile wörtlich, keine WARN),
  `test_unreadable_previous_allowlist_is_warn` (Datei mit `{` ⇒ WARN mit Pfad),
  `test_shrink_check_runs_in_dry_run_without_write` (`--dry-run` mit vorheriger Datei ⇒ WARN
  vorhanden, Datei-Bytes unverändert),
  `test_allowlist_is_written_with_version_two` (voller Sync ⇒ `version == 2`,
  `authority_overrides`-Key vorhanden, **auch ohne Grant** `{}` — K-10),
  `test_check_mode_stays_rc_zero_on_shrink` (OQ-4: `--dry-run --check` ⇒ rc 0 trotz WARN).
  Lauf → **rot — 10 failed**.
- [ ] Step 2: Vor dem `dry_run`-`return` (`:1922-1924`) den Vergleich einbauen:
  Datei lesen (`json.load`), bei `FileNotFoundError` INFO, bei `json.JSONDecodeError`/`OSError`
  WARN; sonst `dropped = sorted(set(previous.get("eligible_roles", [])) - set(resolved["eligible_roles"]))`
  und bei `dropped` die WARN-Zeile bauen: Rollen sortiert, je `role (reason)`, auf 20 Einträge
  begrenzen, Rest `… (+N more)`.
- [ ] Step 3: `_shrink_reasons` mit der **disjunkten** Definition aus K-5/Spec §3.5
  implementieren — Prüfreihenfolge `grant withdrawn` → `role removed` → `gate-dropped` →
  `no Bash`; `no Bash` nur, wenn die Rolle in `roles:` steht (sonst greift bereits
  `role removed`). `no Bash` nutzt
  `effective_commit_authority(role, agent_meta_root, None, resolved.get("authority_overrides"))`.
- [ ] Step 4: Moduswechsel-Zeile separat **vor** der Schrumpf-Zeile emittieren, wenn
  `previous.get("mode") not in (None, "off")` und `resolved["mode"] == "off"`; Rollenzahl = Länge
  der **vorherigen** Liste.
- [ ] Step 5: Docstring der Stage (`:1894-1907`) ergänzen: der Vergleich ist read-only, läuft
  damit auch im Dry-Run, die Gründe sind disjunkt definiert, und `version: 2` ist additiv
  (Leser tolerieren `version: 1`; der Hook liest `mode`/`eligible_roles`/`authority_overrides`,
  `hooks/1-generic/orchestrator-guard-impl.sh:448-478`).
- [ ] Step 6: Verifikation: **grün — 10 passed**; `python3 -m pytest
  tests/test_auto_commit_allowlist_pipeline.py tests/test_active_set.py --basetemp="$PYTEST_BASETEMP" -q`
  → 0 failed; `python3 scripts/sync.py --dry-run --check` → rc 0.
- [ ] Step 7: Commit `feat: warn when the auto-commit allowlist shrinks`.

### T10 — Admin-UI: `auto_commit`-Key-Round-Trip erhalten (M5, S)

**Agent:** developer
**Depends on:** T1
**Files:**
- Modify: `docs/ui/admin-ui.html` (`viewProjectAutoCommit`, `:7639-7766`)
- Create: `tests/test_admin_ui_auto_commit_section.py`

**Interfaces:** Produces `out` als Spread des geklonten Blocks (`{ ...ac, mode }`), damit
unbekannte Keys (heute `authority_overrides`, künftig weitere) beim Save erhalten bleiben;
Consumes `clone`/`saveProjectSection` (`:7650`, `:7761`).

- [ ] Step 1: **Test zuerst** in `tests/test_admin_ui_auto_commit_section.py` (Text-Pinning,
  Muster `tests/test_admin_ui_git_section.py:1-30`): `test_save_preserves_unknown_keys`
  (HTML-Quelle enthält `const out = { ...ac, mode };` und **nicht** `const out = { mode };`),
  `test_auto_commit_view_mentions_authority_overrides` (Hilfetext im Pane nennt
  `authority_overrides` + „edit in project.yaml"), `test_help_text_pinned`
  (`docs/api/admin-ui-reference.md` enthält `authority_overrides`).
  Lauf → **rot — 3 failed**.
- [ ] Step 2: In `:7753` `const out = { ...ac, mode };` setzen — die folgenden Zuweisungen
  (`triggers`, `file_count_threshold`, `custom_script`, `secret_scan`) bleiben unverändert und
  überschreiben damit weiterhin bewusst. Kein Feld-Editor (F-2).
- [ ] Step 3: Hilfetext im Pane (`:7642-7647`) um einen Satz ergänzen: Grant ist YAML-only
  (Formular folgt, Issue F-2) und wird beim Speichern nicht gelöscht.
- [ ] Step 4: Verifikation: **grün — 3 passed**; `python3 -m pytest
  tests/test_admin_ui_git_section.py tests/test_admin_ui_plugins_section.py --basetemp="$PYTEST_BASETEMP" -q`
  → 0 failed (Text-Anker anderer Panes unberührt).
- [ ] Step 5: Commit `fix: keep unknown auto-commit keys when the admin panel saves`.

### T11 — Doku: README, Admin-UI-Referenz, CHANGELOG, #767-Anker (M5, M)

**Agent:** technical-writer
**Depends on:** T8, T9, T10
**Files:**
- Modify: `README.md` (`:477-500`)
- Modify: `docs/api/admin-ui-reference.md` (`:181-185`)
- Modify: `templates/configs/project.yaml.example` (`# auto_commit:`, `:91`)
- Modify: `CHANGELOG.md` (`Unreleased`, `:3`)
- Modify: `docs/specs/767-auto-commit-permission-authority.md` (nur Zeilenanker, F-3)

**Interfaces:** Consumes die finalen Log-Formate (Spec §4.6), die Präzedenz (Spec §4.2) und die
Allowlist-Form (Spec §4.4); Produces ausschließlich Prosa.

- [ ] Step 1: **Test zuerst** (Doku-Greps als Testkommando, keine neue Testdatei):
  `grep -c "authority_overrides" README.md docs/api/admin-ui-reference.md templates/configs/project.yaml.example`
  ⇒ je ≥ 1; `grep -n "acknowledge_full_shell" README.md templates/configs/project.yaml.example`
  ⇒ je ≥ 1; `grep -n "permission-mode-overrides" README.md` ⇒ Treffer im Auto-commit-Abschnitt;
  `grep -n "active-set" README.md` ⇒ Treffer; `grep -c "#1181" CHANGELOG.md` ⇒ ≥ 1;
  `grep -n "orchestrator-guard" README.md` ⇒ Treffer (Guard-Gate).
  Diese Befehle sind der Abnahmeschritt (rot vor Step 2–5).
- [ ] Step 2: `README.md`-Abschnitt „Auto-commit" (`:477-500`): Grant-Beispiel (YAML, Objektform
  mit `acknowledge_full_shell: true`), Eskalationsregel (`delegate`/`notify` → `direct`, keine
  Rücknahme), **Präzedenz** gegen `permission-mode-overrides` (orthogonal,
  `scripts/lib/roles.py:565-577`) und `active-set` (gate-dropped = stiller Verlust mit INFO,
  `scripts/lib/active_set.py:59-67`), Gate-Tabelle: **Render nur mit (a) verifiziertem
  Hook-Protokoll und (b) aktivem Guard** (Claude/Gemini ja; Opencode/Continue/Copilot/ZCode/
  KimiCode/Mammouth/Codex nein — `config/ai-providers.yaml:26-27, 175-176, 274, 444, 539, 622,
  734, 813, 895`), und die **Sicherheitsaussage** wörtlich: „Der Grant ist eine bewusste
  Voll-Shell-Ausweitung, keine `git`-Beschränkung; der Guard-Hook begrenzt Sentinel-tragende
  Kommandos auf `git add` und ein nicht-amendierendes `git commit`. Kommandos ohne Sentinel kann
  er keiner Rolle zuordnen (F-5)."
- [ ] Step 3: `docs/api/admin-ui-reference.md` (`:181-185`): `authority_overrides` als
  YAML-only-Feld dokumentieren (Objektform + Pflicht-Ack), inkl. „Panel erhält unbekannte Keys
  beim Speichern" und dem Hinweis auf F-2.
- [ ] Step 4: `templates/configs/project.yaml.example` (`:91`): im `# auto_commit:`-Kommentarblock
  ein auskommentiertes `authority_overrides`-Beispiel mit `authority: direct` und
  `acknowledge_full_shell: true` plus einem Satz zur Shell-Ausweitung ergänzen.
- [ ] Step 5: `CHANGELOG.md` unter `Unreleased` (`:3`): **Added** (neuer Key, Grant-Zeile,
  Grant-/Shrink-/Notice-Logs, `hook_state`-Prädikat), **Changed** (`ALLOWLIST_VERSION` 1→2 wird
  bei **jedem** Sync geschrieben — auch ohne Grant, K-10), **Security** (Voll-Shell-Ausweitung,
  Pflicht-Ack, Guard-/Hook-Gate, Sentinel-Härtung, Attributionslücke F-5, Rollout-Hinweis auf
  #1151).
- [ ] Step 6: F-3: In `docs/specs/767-auto-commit-permission-authority.md` die veralteten
  `datei:zeile`-Anker auf die heute gültigen ziehen (`auto_commit.py:14→:28`,
  `:32-39→:127-143`, `:85-169→:322-459`, `config.py:1302-1315→:1792-1848`,
  `sync_pipeline.py:1479-1494→:1893-1924`,
  `hooks/1-generic/orchestrator-guard-impl.sh:201-232→:420-502`). **Nur** Anker, kein Inhalt.
- [ ] Step 7: Verifikation: die Greps aus Step 1 sind grün;
  `python3 -m pytest tests/test_docs_crossrefs.py --basetemp="$PYTEST_BASETEMP" -q` (sofern
  vorhanden; sonst `python3 scripts/consistency-check.py` → keine neuen ERROR).
- [ ] Step 8: Commit `docs: document the opt-in commit authority grant`.

### T12 — Szenario 94 (Grant an/aus) + Registry (M6, M)

**Agent:** developer
**Depends on:** T8, T9, T11
**Files:**
- Create: `tests/scenarios/configs/94-auto-commit-authority-grant.project.yaml`
- Create: `tests/scenarios/asserts/94-auto-commit-authority-grant.sh`
- Modify: `tests/scenarios/registry.md` (Tabelle nach `:132`, Konvention `:16-25`)

**Interfaces:** Consumes das Szenario-Harness (`tests/scenarios/run.sh`) und
`18-auto-commit.project.yaml` als Basis (`roles:` enthält bereits `documenter`); Produces ein
PASS-Szenario mit echten Assertions.

- [ ] Step 1: **Assert zuerst** (`tests/scenarios/asserts/94-auto-commit-authority-grant.sh`,
  ausführbar, `REPO_ROOT` in der Env): prüft
  (a) `.claude/agents/documenter.md` enthält `- Bash` im Frontmatter und die Grant-Zeile mit
  `full `Bash` grant, not a `git`-only grant`,
  (b) `.claude/agents/planner.md` (nicht gegrantet, `notify`) enthält **kein** `Bash` und
  **kein** `#1181`,
  (c) `.opencode/agents/documenter.md` enthält `bash: deny` (hook-loser Provider ⇒ kein
  Render-Grant) und `sync.log` die `auto-commit-grant:`-WARN-Zeile,
  (d) `.meta-config/auto-commit-allowlist.json` hat `"version": 2` und
  `authority_overrides.documenter == "direct"`,
  (e) ein zweiter Sync mit einer Kopie der Config **ohne** `authority_overrides` erzeugt eine
  `auto-commit-allowlist: eligible_roles shrank`-WARN-Zeile mit `documenter (grant withdrawn)`,
  (f) ein dritter Sync mit `hooks: {orchestrator-guard: {enabled: false}}` rendert in
  `.claude/agents/documenter.md` **kein** `Bash` (N-1).
  Lauf: `tests/scenarios/run.sh 94` → **FAIL** (Szenario fehlt noch).
- [ ] Step 2: `tests/scenarios/configs/94-auto-commit-authority-grant.project.yaml` anlegen —
  `roles: [orchestrator, developer, tester, git, documenter, planner]`,
  `ai-providers: [Claude, Opencode]`,
  `auto_commit: {mode: auto, triggers: [task-boundary], authority_overrides: {documenter:
  {authority: direct, acknowledge_full_shell: true}}}`,
  `dod-preset`/`platforms` wie `18-auto-commit`.
- [ ] Step 3: `registry.md`-Zeile ergänzen:
  `| \`94-auto-commit-authority-grant\` | Claude, Opencode | strict (default) | \`auto_commit.authority_overrides\` (Issue #1181): Grant (mit Pflicht-Ack) eskaliert \`documenter\` → \`direct\` (Allowlist v2 + \`Bash\`-Render, Grant-Zeile), hook-loser Provider warnt statt zu rendern, deaktivierter Guard rendert nichts, Nicht-Grant-Rollen bleiben byte-identisch, Schrumpf-Warnung mit disjunktem Grund |`
- [ ] Step 4: Verifikation: `tests/scenarios/run.sh 94` → **PASS**; `tests/scenarios/run.sh 18 19 20 21`
  → **PASS** (keine Regression der Auto-commit-Szenarien).
  **Ergänzungsbefund aus T12 im Plan fortschreiben:** Szenario-IDs sind abgestimmt, 94 ist frei
  (letzte heute `93`, `registry.md:132`); `95–98` sind für #1187 reserviert.
- [ ] Step 5: Commit `test: pin the authority grant as scenario 94`.

### T13 — Voller End-to-End-Lauf im Scratch-Consumer (M6, M)

**Agent:** senior-developer
**Depends on:** T12
**Files:**
- Create (nur Arbeitskopie, untracked): `.tmp/scenario-authority-1181/.meta-config/project.yaml`,
  `.tmp/scenario-authority-1181/` (generierte Provider-Bäume, `sync.log`)

**Interfaces:** Consumes den Branch-Stand (alle Tasks bis T12), `documenter` als Referenzrolle
(AC-1), den Guard-Hook (`hooks/1-generic/orchestrator-guard-impl.sh:448-478`); Produces den
abschließenden Nachweis inkl. erzwungener Schrumpfung.

- [ ] Step 1: Scratch-Consumer anlegen: `.meta-config/project.yaml` mit
  `project: {name: scenario-authority-1181, prefix: s1181}`, `ai-providers: [Claude, Opencode]`,
  `roles: [orchestrator, developer, documenter, planner]`,
  `auto_commit: {mode: auto, triggers: [task-boundary], authority_overrides: {documenter:
  {authority: direct, acknowledge_full_shell: true}}}`,
  `agent-meta-version: aaed14c2`.
- [ ] Step 2: Lauf mit Grant:
  `cd .tmp/scenario-authority-1181 && python3 "$OLDPWD/scripts/sync.py"` → rc 0; dann prüfen:
  (1) `.claude/agents/documenter.md` Frontmatter enthält `Bash`, (2) Body enthält die
  Grant-Zeile, (3) `sync.log` enthält genau eine
  `auto-commit-grant: documenter=direct (source: auto_commit.authority_overrides; hook-enforced: yes)`,
  (4) `sync.log` enthält die `not enforced on provider 'Opencode'`-WARN exakt einmal,
  (5) `.meta-config/auto-commit-allowlist.json` → `version == 2`,
  `eligible_roles` enthält `documenter`, `authority_overrides == {"documenter": "direct"}`.
- [ ] Step 3: Guard-Sentinel real prüfen (AC-2, ohne Provider-Runtime): den generierten
  `.claude/agents/documenter.md` als Rollenquelle nehmen und den Hook mit einem synthetischen
  Payload starten —
  `printf '{"tool_name":"Bash","tool_input":{"command":"#agent-meta:agent=documenter\\ngit add -A && git commit -m \\"x\\""},"cwd":"<scratch>"}' | bash hooks/1-generic/orchestrator-guard-impl.sh`
  ⇒ **rc 0**; Kontrolllauf mit `git push origin main` im selben Sentinel ⇒ **rc 2**; Kontrolllauf
  mit `curl https://example.invalid` im selben Sentinel ⇒ **rc 2** (N-3, Grant-Härtung).
- [ ] Step 4: Schrumpfung erzwingen: `authority_overrides` aus der Scratch-Config entfernen und
  erneut syncen ⇒ `sync.log` enthält
  `auto-commit-allowlist: eligible_roles shrank <alt> -> <neu> (-1): documenter (grant withdrawn)`,
  `eligible_roles` ohne `documenter`, und der regenerierte `.claude/agents/documenter.md` hat
  **kein** `Bash` mehr (Rollback-Beweis, §9).
- [ ] Step 5: Guard-Fail-closed real prüfen: `hooks: {orchestrator-guard: {enabled: false}}` in
  die Scratch-Config setzen, erneut syncen ⇒ kein `Bash` im generierten Agenten, die
  `guard hook disabled`-WARN im `sync.log`, `python3 scripts/sync.py --validate` in der
  Scratch-Wurzel ⇒ **rc 1** (N-1).
- [ ] Step 6: Aufräumen: `.tmp/scenario-authority-1181/` bleibt als Beleg liegen (untracked,
  `git status --porcelain` darf nur `.tmp/` zeigen); **kein** Commit in diesem Task.
- [ ] Step 7: Verifikation: alle Punkte aus Step 2–5 sind belegt (fünf Artefakt-Prüfungen,
  drei Sentinel-Läufe, Schrumpf-Nachweis, Guard-Fail-closed); die Befehlsausgaben in den
  Task-Report (nicht in den Plan) übernehmen.

### T14 — Gesamtabnahme, Baseline-Vergleich, `--check` (M6, S)

**Agent:** validator
**Depends on:** T1–T13, T15, T16
**Files:** — (Verifikation); ggf. Nachbesserungs-Ticket im Report.

**Interfaces:** Consumes die Baseline `baseline-validate.txt` (`EXIT=0`) und
`baseline-check.txt:1-6` (fünf erwartete Warnungen); Produces den Abnahme-Report.

- [ ] Step 1: `python3 -m pytest tests/test_hook_state.py tests/test_auto_commit_schema.py
  tests/test_auto_commit_lib.py tests/test_auto_commit_block_render.py
  tests/test_auto_commit_violations.py tests/test_auto_commit_allowlist_pipeline.py
  tests/test_auto_commit_coverage.py tests/test_auto_commit_developer_reference.py
  tests/test_auto_commit_authority_grants.py tests/test_orchestrator_guard_hook.py
  tests/test_admin_ui_auto_commit_section.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**
  (Bestand 75 laut §8: 3 + 20 + 4 + 1 + 17 + 12 + 18; dazu die neuen Tests der Tasks
  T1/T2/T3/T4/T5/T6/T7/T8/T9/T10/T15/T16).
- [ ] Step 2: `python3 scripts/sync.py --validate` → **rc 0**, keine neuen `[ERROR]`-Zeilen
  gegenüber `baseline-validate.txt`.
- [ ] Step 3: `python3 scripts/sync.py --dry-run --check` → **rc 0**; die Warnliste enthält
  höchstens die fünf erwarteten Einträge aus `baseline-check.txt:1-6` (OQ-4: Schrumpf-Warnung
  ist WARN, kein CI-Gate).
- [ ] Step 4: `git diff --name-only aaed14c2..HEAD -- agents/` → **leer** (AC-1: keine Datei
  unter `agents/` editiert; commit-fest, K-16/RVW2-1181-02).
- [ ] Step 5: `tests/scenarios/run.sh` (alle) → **PASS** (mindestens `94` neu grün, keine
  Regression in `18`–`21`).
- [ ] Step 6: Abnahme-Report: AC→Task-Traceability aus §11 mit Beleg je AC **und** N-1…N-4 aus
  Spec §10; offene Punkte (OQ-1…OQ-6, OQ-P3) mit Entscheidungsstatus.
- [ ] Step 7: **DoD-Nachweis (K8):** Bestätigen, dass `config/project-config.schema.json`
  (`auto_commit.properties.authority_overrides`) und `scripts/lib/auto_commit.py:164` (`_KEYS`)
  im **selben** PR/Commit gelandet sind, und `test_enum_constants_match_schema` grün ist
  (`schema.properties.auto_commit.properties == _KEYS`). Ein PR, der nur das Schema erweitert,
  ist **nicht** abnahmefähig — er deaktiviert #1181 per Fail-Safe.

### T15 — `hook_state`: ein Prädikat für die effektive Hook-Aktivierung (M1, S)

**Agent:** developer
**Depends on:** —
**Files:**
- Create: `scripts/lib/hook_state.py`
- Modify: `scripts/lib/hooks.py` (`sync_hooks`, `:621-626`)
- Create: `tests/test_hook_state.py`

**Interfaces:** Produces
`ORCHESTRATOR_GUARD_HOOK = "orchestrator-guard"`,
`ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT = True`,
`resolve_hook_enabled(hooks_config: Mapping, hook_stem: str, enabled_by_default: bool = False) -> tuple[bool, bool]`
und `guard_hook_enabled(config: dict) -> tuple[bool, bool]`; Consumes nichts (importfreies Modul).

- [ ] Step 1: **Test zuerst** in `tests/test_hook_state.py`:
  `test_guard_default_is_enabled` (`guard_hook_enabled({}) == (True, False)` — Default aus
  `hooks/1-generic/orchestrator-guard.sh:7`),
  `test_guard_explicit_false_disables` (`{"hooks": {"orchestrator-guard": {"enabled": False}}}`
  ⇒ `(False, False)`; RVW-1181-01),
  `test_guard_quoted_false_is_invalid_and_disabled`
  (`{"hooks": {"orchestrator-guard": {"enabled": "false"}}}` ⇒ `(False, True)` — Strict-Bool wie
  `_strict_enabled`, `hooks.py:447-456`),
  `test_resolve_uses_enabled_by_default_flag` (`resolve_hook_enabled({}, "x", True) == (True, False)`
  und `resolve_hook_enabled({}, "x") == (False, False)`),
  `test_resolve_ignores_other_hooks` (`{"dod-push-check": {"enabled": True}}` ⇒ Guard-Default
  unberührt).
  Lauf → **rot — 5 failed** (`ModuleNotFoundError`).
- [ ] Step 2: `scripts/lib/hook_state.py` implementieren — nur `typing`/`collections.abc`,
  keine Repo-Imports (damit `hooks.py` und `auto_commit.py` es ohne Zyklus laden können).
- [ ] Step 3: `hooks.sync_hooks` (`:621-626`) auf `resolve_hook_enabled(project_hooks_cfg,
  hook_stem, enabled_by_default)` umstellen und die bestehende Warnung bei `invalid` mit
  unverändertem Text ausgeben (`f"hooks.{hook_stem}.enabled: expected true/false (bool), got
  {raw!r} ({type(raw).__name__}) — treated as disabled"`).
- [ ] Step 4: Verifikation: **grün — 5 passed**; Regression
  `python3 -m pytest tests/test_hook_managed_index.py tests/test_provider_hooks_config.py
  --basetemp="$PYTEST_BASETEMP" -q` → 0 failed (Hook-Sync-Verhalten unverändert);
  `python3 scripts/sync.py --dry-run` → rc 0.
- [ ] Step 5: Commit `refactor: share one hook-enablement predicate`.

### T16 — Hook-Härtung: Grant-Sentinel nur für `git add`/`git commit` (M4, L)

**Agent:** senior-developer
**Depends on:** T9
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` (`:1282-1326`, `:1336`, Gate neben `:1535`,
  `# version:` `:2`)
- Modify: `tests/test_orchestrator_guard_hook.py`

**Interfaces:** Produces im Klassifizierer ein viertes Ausgabefeld `all_git`
(`1`, wenn jedes Statement mit `git` beginnt, sonst `0`), die Shell-Variable `_GIT_SCAN_ALL_GIT`
und `IS_GRANT_SENTINEL` (Rolle steht in der Allowlist unter `authority_overrides`); Consumes das
v2-Artefakt aus T9 (`authority_overrides`-Map) und die bestehende Sentinel-Elevation
(`:418-481`). Öffentlicher Contract: Spec §3.3.1 und die Hook-Zeile in §4.6.

- [ ] Step 1: **Test zuerst** in `tests/test_orchestrator_guard_hook.py`
  (`_write_allowlist` um `authority_overrides=None` erweitert):
  `test_granted_role_sentinel_accepts_git_add_and_commit`
  (`authority_overrides={"documenter": "direct"}`, `eligible_roles=["documenter"]`;
  `#agent-meta:agent=documenter\ngit add -A && git commit -m 'x'` ⇒ rc 0),
  `test_granted_role_sentinel_blocks_curl` (gleiche Allowlist; `#agent-meta:agent=documenter\ncurl
  https://example.invalid` ⇒ **rc 2**, stderr enthält
  ``a granted commit role may only use its sentinel for `git add`/`git commit` ``),
  `test_granted_role_sentinel_blocks_mixed_command` (`git add -A && curl https://example.invalid`
  ⇒ rc 2; das `all_git`-Feld, nicht nur der Mutations-Scope),
  `test_granted_role_sentinel_blocks_push` (`git add -A && git push origin main` ⇒ rc 2),
  `test_granted_role_sentinel_blocks_amend` (`git commit --amend -m 'x'` ⇒ rc 2),
  `test_non_granted_allowlisted_role_keeps_full_shell` (Allowlist ohne `authority_overrides`,
  `eligible_roles=["developer"]`; `#agent-meta:agent=developer\npytest -q` ⇒ rc 0 — native
  `direct`-Rollen bleiben unberührt, AC-3),
  `test_granted_role_without_sentinel_is_unchanged` (`pytest -q` ohne Sentinel ⇒ rc 0; belegt
  die Attributionslücke F-5 als bewusst dokumentierte Grenze),
  `test_v1_allowlist_without_grant_field_keeps_full_shell` (Datei ohne `authority_overrides` ⇒
  wie heute).
  Lauf → **rot — 8 failed**.
- [ ] Step 2: Klassifizierer (`:1282-1326`): `all_git = True` initial, im Statement-Loop auf
  `False`, sobald `cmd != "git"`; Ausgabe als viertes Feld (`print(f'{category} {scope} {bom}
  {1 if all_git else 0}')`). Shell-Validierung von `NF == 3` auf `NF == 4` (`:1336`) und
  `_GIT_SCAN_ALL_GIT=$(... awk '{print $4}')` ergänzen.
- [ ] Step 3: In der Sentinel-Elevation (`:465-478`) zusätzlich prüfen, ob `_ROLE` ein Key in
  `data.get("authority_overrides", {})` ist ⇒ `IS_GRANT_SENTINEL=1` (eigener Flag, **nicht**
  `IS_ALLOWLIST_SENTINEL` wiederverwenden, damit die bestehende Gate-Logik unverändert bleibt).
- [ ] Step 4: Neues Gate direkt **nach** dem Mutations-Gate (`:1547`), nur für
  `IS_GRANT_SENTINEL=1`: erlaubt ist ausschließlich `_GIT_SCAN == "mutation"` **und**
  `_GIT_SCAN_SCOPE == "narrow"` **und** `_GIT_SCAN_ALL_GIT == "1"`; sonst stderr-Meldung
  (Spec §4.6) + `exit 2`. Der Block läuft **vor** `exit 0`, damit kein Pfad daran vorbeiführt.
  Bewusst mit erfasst: `git status`, `git log` und jeder andere Nicht-`add`/`commit`-Aufruf fallen
  hier durch — der Sentinel ist für eine Grant-Rolle ausschließlich der Commit-Pfad (Spec §3.3.1
  Punkt 2). Das steht als Kommentar am Gate, damit es niemand als Fehler „repariert“.
- [ ] Step 5: `# version: 1.11.0` → `1.12.0` (`:2`) plus Changelog-Satz in derselben Zeile
  (Konvention wie `:3`).
- [ ] Step 6: Verifikation: **grün — 8 passed**; Regression
  `python3 -m pytest tests/test_orchestrator_guard_hook.py --basetemp="$PYTEST_BASETEMP" -q`
  → 0 failed (alle bestehenden Sentinel-/Strict-Mode-/Mutations-Fälle unverändert);
  `bash -n hooks/1-generic/orchestrator-guard-impl.sh` → rc 0.
- [ ] Step 7: Commit `feat: restrict a granted sentinel to git add and commit`.

---

## 7. Interfaces und Signaturen

### 7.0 `scripts/lib/hook_state.py` (neu)

```python
ORCHESTRATOR_GUARD_HOOK = "orchestrator-guard"
ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT = True

def resolve_hook_enabled(
    hooks_config: Mapping,
    hook_stem: str,
    enabled_by_default: bool = False,
) -> tuple[bool, bool]:
    """(enabled, invalid_value) — nur ein echtes bool True aktiviert (#1155)."""

def guard_hook_enabled(config: dict) -> tuple[bool, bool]:
    """resolve_hook_enabled für ORCHESTRATOR_GUARD_HOOK, Default True."""
```

`scripts/lib/hooks.py::sync_hooks` und `scripts/lib/auto_commit.py` konsumieren ausschließlich
diese Funktionen (K-9).

### 7.1 `scripts/lib/auto_commit.py`

```python
ALLOWLIST_VERSION = 2                                   # war 1 (:31)

_KEYS = {"mode", "triggers", "file_count_threshold", "custom_script",
         "secret_scan", "authority_overrides"}           # (:164) + neuer Key

def normalize_authority_overrides(raw: object) -> dict[str, str]:
    """{role: "direct"} aus der Config-Objektform. Nur Einträge mit
    authority == "direct" AND acknowledge_full_shell is True. Wirft nie."""

def effective_commit_authority(
    role: str,
    agent_meta_root: Path,
    platform: str | None = None,
    authority_overrides: Mapping[str, str] | None = None,
) -> str:
    """delegate|notify -> direct nur bei wanted == 'direct'; sonst derived.
    Erwartet die NORMALISIERTE Map; ein Nicht-Mapping wird wie None behandelt.
    Wirft nie; Validierung ist Sache von authority_override_violations."""

def is_role_eligible(
    role: str,
    agent_meta_root: Path,
    platform: str | None = None,
    authority_overrides: Mapping[str, str] | None = None,   # NEU, Default None
) -> bool: ...

def authority_override_violations(
    config: dict,
    agent_meta_root: Path,
    provider_config: Mapping | None = None,   # ai-providers.yaml; None => selbst laden
) -> list[str]:
    """Harte Grant-Verstöße (Form, Ack, Rolle, Nicht-Durchsetzbarkeit).
    Jede Meldung beginnt mit 'auto_commit.authority_overrides.'."""

def authority_override_notices(
    config: dict,
    active_roles: Iterable[str],
) -> list[str]:
    """INFO: Grant auf inaktive Rolle (kein Fehler).
    active_roles = effektive aktive Menge (raw ∩ ActiveSet.has, K-15)."""

def resolve_commit_grant(
    role: str,
    resolved: dict,
    provider_capabilities: dict | None,
    agent_meta_root: Path,          # K-1
    *,
    guard_enabled: bool,            # K-9
) -> tuple[str, bool]:
    """(authority für diesen Provider, render_bash).
    render_bash == True nur bei mode in {auto,custom} AND Grant AND guard_enabled
    AND provider_hooks_supported(pc) AND 'Bash' nicht schon im Template (K-3)."""

def render_auto_commit_block(
    resolved: dict,
    authority: str = AUTHORITY_DIRECT,
    *,
    role: str | None = None,
) -> str: ...                        # role=None => byte-identisch zu heute
```

`resolve_auto_commit_config` liefert zusätzlich `"authority_overrides": {role: "direct", …}`
(normalisierte Map, nur Rollen aus `active_roles`) und im Fail-Safe `"authority_overrides": {}`.

### 7.2 Schema-Fragment (`config/project-config.schema.json`, `auto_commit.properties`)

```json
"authority_overrides": {
  "type": "object",
  "description": "Issue #1181: opt-in commit-authority grant per role. Escalates a write-capable role (delegate/notify) to 'direct' for the guard-hook sentinel and the rendered permission. Every entry MUST acknowledge that the grant is a full Bash grant, not a git-only grant. Default: {} (no grant, rendering unchanged). Only valid for roles that already have Edit/Write; a read-only role is a configuration error.",
  "propertyNames": { "pattern": "^[a-z0-9][a-z0-9-]*$" },
  "additionalProperties": {
    "type": "object",
    "additionalProperties": false,
    "required": ["authority", "acknowledge_full_shell"],
    "properties": {
      "authority": { "type": "string", "enum": ["direct"] },
      "acknowledge_full_shell": { "type": "boolean", "const": true }
    }
  },
  "default": {}
}
```

`auto_commit.additionalProperties` bleibt `false` (`:1546`) — der Key **muss** in `properties`
stehen; `_KEYS` wird parallel gepflegt, Wächter ist
`tests/test_auto_commit_violations.py:111-123`.

### 7.3 Allowlist-v2-Struktur (`.meta-config/auto-commit-allowlist.json`)

```json
{
  "authority_overrides": { "documenter": "direct" },
  "custom_script": null,
  "eligible_roles": ["developer", "documenter", "tester"],
  "file_count_threshold": 5,
  "mode": "auto",
  "secret_scan": true,
  "triggers": ["task-boundary"],
  "version": 2
}
```

Sortierung kommt aus `json.dumps(..., sort_keys=True)` (`sync_pipeline.py:1924`) — `version`
steht daher **nicht** am Ende. Leser: der Hook liest `mode`, `eligible_roles` **und** seit T16
`authority_overrides` (`hooks/1-generic/orchestrator-guard-impl.sh:448-478`); `version: 1` bleibt
lesbar (T9-Step 2 toleriert fehlende Schlüssel per `.get`). Das Artefakt enthält auch ohne Grant
`"authority_overrides": {}` und `"version": 2` (K-10).

### 7.4 Log-Formate (Contract, stabil präfixiert)

| Kanal | Format | Bedingung |
|---|---|---|
| WARN | `auto-commit-allowlist: eligible_roles shrank <old> -> <new> (-<n>): <role> (<reason>), …` | vorherige Datei vorhanden und `dropped != ∅` |
| WARN | `auto-commit-allowlist: mode changed <old> -> off; all <n> eligible role(s) dropped` | Moduswechsel auf `off` |
| INFO | `auto-commit-allowlist: no previous allowlist — shrink check skipped` | Datei fehlt |
| WARN | `auto-commit-allowlist: previous allowlist unreadable at <path> — shrink check skipped` | JSON-/IO-Fehler |
| INFO | `auto-commit-grant: <role>=direct (source: auto_commit.authority_overrides; hook-enforced: yes)` | Grant + Hook-Provider **und** aktiver Guard |
| WARN | `auto-commit-grant: <role>=direct not enforced on provider '<P>' (has_hooks=false); rendered as <derived> (issue #1181)` | Grant + hook-loser Provider |
| WARN | `auto-commit-grant: <role>=direct not enforced (guard hook disabled: hooks.orchestrator-guard.enabled is not true); rendered as <derived> (issue #1181)` | Grant + deaktivierter Guard |
| INFO | ``auto-commit-grant: <role>=direct ignored — role is not active (not listed in `roles:` or dropped by the active set)`` | Grant auf inaktive Rolle |
| ERROR (`--validate`) | `config-audit [ERROR] auto_commit: auto_commit.authority_overrides.<…>` | semantischer Grant-Verstoß inkl. Nicht-Durchsetzbarkeit |
| Hook stderr + rc 2 | ``ORCHESTRATOR_GUARD: a granted commit role may only use its sentinel for `git add`/`git commit` (issue #1181).`` | Grant-Sentinel ohne reinen `git add`/`commit`-Scope (T16) |

`<reason>` ∈ `grant withdrawn` \| `role removed` \| `gate-dropped` \| `no Bash` — **disjunkt**
definiert (K-5), Prüfreihenfolge wie in der Spalte genannt. Rollenliste max. 20 Einträge, Rest
`… (+N more)`.

## 8. Teststrategie

**Bestand (nicht verändern, als Regressionsanker):** **75** Tests in sieben Dateien, Zahlen aus
einem echten Lauf gegen `aaed14c2` (per `grep -c 'def test_'` je Datei nachgezählt, Review
RVW-1181-06):

| Datei | Tests |
|---|---|
| `test_auto_commit_allowlist_pipeline.py` | 3 |
| `test_auto_commit_block_render.py` | 20 |
| `test_auto_commit_coverage.py` | 4 |
| `test_auto_commit_developer_reference.py` | 1 |
| `test_auto_commit_lib.py` | 17 |
| `test_auto_commit_schema.py` | 12 |
| `test_auto_commit_violations.py` | 18 |
| **Summe** | **75** |

Dazu die Hook-Fälle in `test_orchestrator_guard_hook.py:945-1058` (eigene Datei, nicht in den 75
enthalten). **Gates stützen sich nicht auf Sollzahlen**, sondern auf `0 failed` plus die je Task
namentlich genannten Tests; die Zahlen hier dienen nur der Plausibilität.

**Neu/erweitert je Grant-Fall (Soll ≈ 40 Tests):**

| Fall | Test (Datei) | Assertion-Kern |
|---|---|---|
| Schema akzeptiert `direct` + Ack | `test_authority_overrides_direct_with_ack_is_valid` (schema) | `jsonschema.validate` ohne Fehler |
| Schema lehnt Skalar/fehlendes Ack/`false`/`notify`/Sub-Key/Tippfehler ab | sechs `test_authority_overrides_*` (schema) | `ValidationError` |
| `_KEYS` == Schema-Properties | `test_enum_constants_match_schema` (violations, **bestehend**) | `set(_KEYS) == set(ac["properties"])` |
| Grant ungültig → Fail-Safe | `test_invalid_grant_triggers_fail_safe`, `…without_ack…` (lib) | `mode == "off"`, `eligible_roles == []`, `authority_overrides == {}` |
| Grant nicht durchsetzbar | `test_grant_not_enforced_when_guard_disabled`, `…on_hookless_provider` (violations) | Meldung exakt Spec §4.3 |
| Grant auf inaktive Rolle | `test_authority_override_inactive_role_is_not_a_violation` (violations) | `[]` + eine INFO-Notice |
| Edit-only granted | `test_notify_role_escalates_to_direct` (grants) | `"direct"` |
| Edit-only not granted | `test_no_override_is_identity` (grants) | Identität über alle Templates |
| Read-only nie | `test_read_only_role_never_escalates` (grants) | `"none"` |
| Provider ohne Hook | `test_hookless_provider_renders_derived_and_warns` (grants) | `bash: deny` + exakte WARN |
| Guard deaktiviert | `test_claude_grant_with_disabled_guard_keeps_bash_deny` (grants) | kein `Bash` + exakte WARN |
| Provider mit `has_hooks` ohne Protokoll | `test_grant_on_provider_without_verified_protocol_does_not_render` (grants) | `(derived, False)` |
| Render-Vertrag Claude/Gemini + synthetischer Hook-Fixture | `test_claude_documenter_gains_bash_when_granted`, `test_gemini_grant_maps_to_run_command`, `test_render_bash_on_synthetic_hook_capable_fixture` (grants) | `Bash` / `run_command` / `render_bash is True`; Opencode real nur `bash: deny` + WARN (K-12) |
| Hook-Sentinel | `test_allowlist_sentinel_accepts_documenter_with_v2_allowlist`, `…still_blocks_push…` (hook) | rc 0 / rc 2 |
| Hook-Härtung | `test_granted_role_sentinel_blocks_curl`, `…blocks_mixed_command`, `…blocks_amend`, `test_non_granted_allowlisted_role_keeps_full_shell` (hook) | rc 2 / rc 2 / rc 2 / rc 0 |
| Hook-Prädikat | fünf `test_guard_*`/`test_resolve_*` (hook_state) | `(enabled, invalid)`-Tupel |
| Shrink | `test_shrink_warning_lists_dropped_roles_with_reasons`, `test_no_bash_reason_requires_role_in_roles` (pipeline) | exakte `[WARN]`-Zeile |
| Admin-UI-Round-Trip | `test_save_preserves_unknown_keys` (admin-ui) | `{ ...ac, mode }` in der Quelle |

**Golden-Test „ohne Grant byte-identisch" (AC-3), zweistufig:**
1. *Unit:* `render_auto_commit_block(r) == render_auto_commit_block(r, role=None)` für alle
   Mode×Authority-Kombinationen (T5).
2. *Integration:* zwei Syncs in zwei Temp-Verzeichnissen (mit/ohne `authority_overrides`) —
   `filecmp`/`diff -r` über alle generierten Agenten außer der gegranteten Rolle, plus
   identische `eligible_roles` (T8). Das Allowlist-Artefakt ist von diesem Diff **ausgenommen**
   (K-10: `version: 2` ist der bewusste Default-Diff).

**Zwischentests je Meilenstein:** siehe §5 (Gate-Spalte). Kein Milestone wird ohne grünes Gate
verlassen.

**Ein voller Szenarientest am Ende (T13):** Scratch-Consumer `.tmp/scenario-authority-1181/`
mit `documenter` als Referenzrolle —
(a) Grant an → generierter Claude-Agent mit `Bash` + Grant-Zeile, Allowlist v2,
`auto-commit-grant:`-INFO genau einmal;
(b) Guard-Sentinel akzeptiert `git add` + `git commit`, lehnt `git push` **und** `curl` ab;
(c) Grant aus + erneuter Sync → `eligible_roles`-Schrumpfung um `documenter` mit
`(grant withdrawn)` im Log und ohne `Bash` im regenerierten Agenten;
(d) Guard aus + erneuter Sync → kein `Bash`, WARN, `--validate` rc 1.
Damit sind AC-1…AC-4 und N-1/N-3 **einmal** end-to-end belegt, nicht nur in Unit-Tests.

## 9. Migration und Rollback

**Migration (Consumer):**
- Ohne `authority_overrides` ändert sich nichts am Render: kein Rollen-Template, kein zusätzliches
  `Bash`, identische `eligible_roles`, identische Block-Bytes (AC-3).
- **Einziger Default-Diff:** die Allowlist wird beim nächsten Sync auf `version: 2` gehoben und
  trägt dann `"authority_overrides": {}` — auch ohne Grant (K-10). Additiv; `version: 1` bleibt
  lesbar (kein Reader prüft `version`; der Hook liest `mode`/`eligible_roles`/`authority_overrides`
  per `.get`). Im `CHANGELOG` als „Changed“ ausgewiesen.
- Ein Projekt, das den Key setzt, erhält beim ersten Sync **eine** WARN-Zeile pro hook-losem
  Provider und **kein** `Bash` (fail-safe statt Prosa-Grant); ist der Guard deaktiviert, wird
  ebenfalls nichts gerendert und `--validate` endet rc 1.
- **Formwechsel:** Es gab nie eine ausgelieferte Skalarform (`documenter: direct`) — die Spec war
  und ist `DRAFT`. Ein Projekt, das die nicht freigegebene Zwischenform gesetzt hat, bekommt
  `auto_commit.authority_overrides.documenter: expected {authority: direct,
  acknowledge_full_shell: true}` und den Fail-Safe; das ist laut, nicht still.
- Upgrade-Reihenfolge: erst Framework (dieser Branch), dann Key setzen. Umgekehrt (Key in einem
  älteren Framework) ⇒ `auto_commit has unknown key(s): authority_overrides` ⇒ Fail-Safe
  `mode: off` + WARN — laut, nicht still.

**Rollback (drei Ebenen):**
1. `authority_overrides` entfernen ⇒ nächster Sync schrumpft `eligible_roles` mit
   `(grant withdrawn)`, der Agent verliert `Bash` (Claude/Gemini) und bleibt/ist auf Opencode
   bereits `bash: deny`; keine Code-Änderung nötig.
2. `auto_commit.mode: off` ⇒ kein Sentinel, kein Block (`auto_commit.py:350-352`,
   Hook `:459-464`); die Grant-Zeile verschwindet mit dem Block.
3. Vollständiger Code-Rollback: `rev-parse` auf `aaed14c2`; die geschriebene Allowlist v2 bleibt
   für den älteren Code lesbar (nur unbekannter Zusatzschlüssel, `sort_keys`-stabil). Der
   Hook-Rollback ist unabhängig (`# version:` 1.12.0 → 1.11.0); `hook_state.py` kann bleiben
   (additives Modul ohne Aufrufer im alten Code).

## 10. Risiken

| # | Risiko | Wirkung | Gegenmaßnahme / Task |
|---|---|---|---|
| R1 | **Grant = volle Shell, nicht nur `git`** | Edit-only-Rolle erhält `Bash`: `curl`-Exfiltration, `rm`, `git push`-Versuche; Injection in Rollen-Output wird zu Code-Execution | Pflicht-Ack (T1/T2); Opt-in pro Rolle; Provider- **und** Guard-Gate (T6/T8); Sentinel-Härtung (T16) begrenzt Sentinel-tragende Kommandos auf `add`/`commit`; Log + Artefakt auditierbar (T9); Doku benennt die Ausweitung (T11) |
| R2 | Hook-Lücken (#1151: F6-04/F6-05) | Die Zusage „nur add/commit" ist schwächer als dokumentiert | Rollout-/Doku-Reihenfolge in T11; Risiko in Doku nennen; kein Auto-Rollout; #1151 **vor** T16 mergen (§3a) |
| R3 | Hook-lose Provider | `direct`-Prosa auf `bash: deny` wäre der #767-Widerspruch | `resolve_commit_grant` rendert dort nichts + WARN (T6/T8) |
| R3b | **Guard im Projekt deaktiviert** | `Bash`-Grant ohne jedes Gate | `guard_hook_enabled` als zweites Render-Gate (T15/T6), WARN + `--validate`-ERROR (T2), Szenario-Assert (f) |
| R3c | **Attributionslücke** (F-5) | Kommandos ohne Sentinel sind keiner Rolle zuordenbar ⇒ keine Security-Boundary gegen Injection | Nirgends als Boundary dokumentiert (T5/T11); Ack-Pflicht; F-5 als Ticket |
| R4 | **Persona-Konflikt `documenter`** („You implement NOTHING" + `Bash`) | Rollen-Selbstverständnis kippt; Agent könnte Shell für Nicht-Commit-Zwecke nutzen | Grant-Zeile nennt die Ausweitung **und** die Grenze (T5); Doku-Absatz (T11); Persona selbst **nicht** anfassen (OQ-3) |
| R5 | **#767-Widerspruch** | Spec #767 sagt „direct-only by design"; #1181 hebt das bedingt auf | Neue Funktion statt Änderung von `role_commit_authority` (K-1/§7.1); Docstring in `is_role_eligible` nennt die Ausnahme; #767 bleibt inhaltlich gültig |
| R6 | Admin-UI droppt den Key (F-2) | Nutzer speichert im Panel und verliert den Grant | T10 (Round-Trip-Erhalt) + F-2 (Feld) |
| R7 | Zwei Key-Listen (Schema + `_KEYS`, F-1) | Vergisst man `_KEYS`, deaktiviert der Fail-Safe die ganze Authority | T1-Step 3 + bestehender Mengengleichheits-Test (`test_enum_constants_match_schema`) |
| R8 | Tippfehler im Rollennamen | Stiller No-op | Semantische Prüfung „abgeleitet `none`" ⇒ `--validate`-ERROR (T2); inaktive Rolle ⇒ INFO (T2) |
| R9 | Schrumpf-Warnung bricht CI | Upgrades würden rot | OQ-4: WARN, kein Exit-Code (T9-Step 6, T14-Step 3) |
| R10 | Reihenfolge-Kollision mit #1186/#1187/#1188 | Hunk-Konflikte in Schema/`config.py`/`agent_sync.py`/`sync_pipeline.py`/`admin-ui.html`/Hook | Kanonische Reihenfolge + Matrix in §3a; ein PR nach dem anderen |
| R11 | `ALLOWLIST_VERSION`-Bump als Churn | Jeder Consumer sieht eine geänderte Allowlist ohne eigenen Grant | Bewusster Default-Diff (K-10), in `CHANGELOG` „Changed“ (T11) und §9 Migration dokumentiert |

## 11. AC → Task-Traceability

| AC | Wortlaut-Kern | Tasks | Nachweis |
|---|---|---|---|
| AC-1 | Config-Key macht Edit-only-Rolle eligibel, ohne `agents/` zu ändern | T1, T2, T3, T4, T13 | Schema-/Grant-Tests; `git diff --name-only aaed14c2..HEAD -- agents/` leer (T14-Step 4, K-16); Scratch-Lauf (T13) |
| AC-2 | Gerenderter Agent honoriert den Grant (Sentinel akzeptiert Commit bzw. dokumentiertes Äquivalent) | T5, T6, T8, T12, T13, T16 | Claude-Frontmatter `Bash` + Grant-Zeile; Hook-Test rc 0/rc 2 inkl. `curl`-Ablehnung (`test_orchestrator_guard_hook.py`); Gemini `run_command`; Szenario 94; Scratch-Lauf |
| AC-3 | Rollen ohne Opt-in behalten `bash: deny`, Default unverändert | T5, T8, T12, T16 | Byte-Golden `role=None`; Integrations-Golden zweier Syncs; Opencode-`bash: deny`-Fälle (T8); native `direct`-Rolle behält volle Shell (T16) |
| AC-4 | Schrumpf von `eligible_roles` erzeugt `sync.log`-Warnung mit Rollenliste | T9, T12, T13 | Exakte WARN-Zeichenkette im Pipeline-Test (disjunkte Gründe); Szenario-94-Assert (e); Scratch-Lauf Step 4 |
| AC-5 | Dokumentation inkl. Präzedenz gegen `permission-mode-overrides` und ActiveSet | T11 | README + `admin-ui-reference.md` + `CHANGELOG` + `project.yaml.example`; Doku-Greps (T11-Step 1) |
| N-1 | Guard deaktiviert ⇒ kein `Bash`, `--validate` rc 1 | T2, T6, T8, T12, T13 | `test_grant_not_enforced_when_guard_disabled`; Sync-Test; Szenario-Assert (f) |
| N-2 | Grant ohne `acknowledge_full_shell: true` ⇒ Config-Fehler | T1, T2, T4 | Schema-Tests; `test_grant_without_ack_triggers_fail_safe`; `--validate` rc 1 |
| N-3 | Sentinel-tragendes Nicht-`git`-Kommando ⇒ rc 2 | T16, T13 | `test_granted_role_sentinel_blocks_curl`/`…mixed_command`; Scratch-Lauf Step 3 |
| N-4 | Grant nirgends durchsetzbar ⇒ `--validate`-ERROR, gemischt ⇒ WARN | T2 | `test_grant_not_enforced_on_hookless_provider`, `test_grant_enforced_on_mixed_provider_set_is_no_violation` |

**Nicht vollständig abdeckbare AC-Teile (bewusst, mit Begründung):**
- AC-2 „Sentinel akzeptiert einen echten `git commit` **zur Laufzeit** beim Provider": in CI nur
  als Hook-Unit-Test mit synthetischem Payload plus Allowlist-Artefakt belegbar (T8/T13/T16). Ein
  echter Provider-Runtime-Test existiert im Repo nicht und wird hier nicht erfunden.
- AC-2-Alternative „constrained commit-only Bash permission": nicht als **Provider**-Permission
  erreichbar, weil kein Provider eine kommando-genaue Bash-Permission belegt (OQ-2;
  `provider_transform.py:895-920` mappt Skalare, v2 nutzt `resource: "*"` `:960-972`). Das
  Äquivalent ist die Hook-Härtung aus T16 — sie gilt nur für Sentinel-tragende Kommandos, und
  genau diese Grenze steht so in Block (T5) und Doku (T11).

## 12. Backlog-Bugs — Einordnung

| Issue | Titel (kurz) | Einordnung | Begründung (gegen den echten Issue-Text) |
|---|---|---|---|
| **#1142** | `invalid auto_commit still exits 0 …, writes the allowlist, missing from --validate summary` | **Abhängig, nicht in-scope** — Vorbedingung für die Doku-Aussage, keine Code-Überlappung | Die Issue nennt drei offene Punkte: (1) `plain sync.py` exit 0 bei schema-invalidem Block, (2) Allowlist wird trotzdem geschrieben, (3) Meldung fehlt im `--validate`-Summary. #1181 erbt den #1091-Fail-Safe unverändert (T4/T9 ändern ihn nicht) und fügt eine **zweite Verstoßklasse** hinzu (semantische Grants, T2), die bereits als `[ERROR]` im Summary landet. Ein „kein Allowlist-Write bei ungültigem Block" oder harte Exit-Codes aus #1142 würden `sync_pipeline.py:1909-1924` umbauen — deshalb **nicht** hier mitlösen, sondern: T9-Step 7 pinnt das heutige Verhalten (Fail-Safe + WARN + Write) als Regressionstest, und T11 formuliert die Doku so, dass sie unter beiden #1142-Ausgängen gilt. |
| **#1151** | `NotebookEdit/MultiEdit/PowerShell bypass containment and strict-mode guards; allowlist drift` | **Sicherheitsabhängigkeit, kein Blocker** | Der Grant stützt seine Zusage auf den Guard-Hook; die Issue belegt F6-04 (fehlende Mutations-Kommandos) und F6-05 (Sentinel ohne `agent_id`). **Korrektur zur Vorversion:** #1181 fasst den Hook jetzt an (T16); beide ändern `hooks/1-generic/orchestrator-guard-impl.sh`, deshalb steht #1151 in der Matrix (§3a) **vor** #1181. T11 nennt die Rollout-/Doku-Reihenfolge (R2). `CHANGELOG.md:12` zeigt, dass ein Teil bereits in `2.0.0-beta.8` geflossen ist. |
| **#1172** | `merges dispatched via orchestrator to git agent are blocked …` | **Unabhängig, abgegrenzt** | Merge/Push/Tag/Branch bleiben ausschließlich `git`-Rolle (Spec §5 Nr. 7; `_PUSH_BOUNDARY_LINE`, `auto_commit.py:51-54`). Berührungspunkt wäre nur `rules/1-generic/use-orchestrator.md`, das #1181 nicht anfasst. Kein Task, keine Abhängigkeit — nur der Satz in T11, dass der Grant nichts an der `git`-Rolle ändert. |

## 13. Neu gemeldete Findings (separate Issues, Nummern folgen im Wave-Overview)

> Keine erfundenen Nummern: die Items werden als eigenständige Issues angelegt; die ID trägt
> das Wave-Overview nach. Bis dahin sind sie hier nur mit `F-n` adressiert.

| ID | Titelvorschlag | Labels | Kern (verifiziert) | Verhältnis zu #1181 |
|---|---|---|---|---|
| **F-1** | `bug(config): auto_commit key allowlist exists twice (schema properties vs. _KEYS)` | `bug`, `config`, `sync`, `P3` | Schema deklariert die Keys (`config/project-config.schema.json:1495-1546`, `additionalProperties: false`), `scripts/lib/auto_commit.py:164` führt dieselbe Menge als `_KEYS`; ein nur im Schema ergänzter Key erzeugt „unknown key(s)" (`:222-224`) und deaktiviert per Fail-Safe (`:269-278`) die gesamte Authority. **Präzisierung:** ein Wächter existiert bereits — `tests/test_auto_commit_violations.py:111-123` asserted `set(_KEYS) == set(ac["properties"])`; der Rest-Risikopfad ist ein lokaler Testlauf, der diesen Test überspringt. Vorschlag: `_KEYS` aus dem Schema ableiten. | Kein Blocker; T1-Step 3 hält beide Listen synchron und nutzt den Test als Gate |
| **F-2** | `bug(admin-ui): saving the auto-commit panel drops keys the form does not know` | `bug`, `config`, `admin-ui`, `P3` | `docs/ui/admin-ui.html:7753-7760` baut `out` neu und sendet nur dieses (`:7761`); jeder unbekannte Key wird still gelöscht. Repro: Key in `project.yaml` setzen, Panel öffnen, „Save" → Key weg. | T10 behebt den **Datenverlust** (Spread); F-2 liefert das **Formularfeld** + Round-Trip-Test |
| **F-3** | `docs(spec): 767 references stale file:line anchors` | `docs`, `P3` | `docs/specs/767-auto-commit-permission-authority.md` zeigt u. a. `auto_commit.py:14`, `:32-39`, `:85-169`, `config.py:1302-1315`, `sync_pipeline.py:1479-1494`, Hook `:201-232`; gültig sind `:28`, `:127-143`, `:322-459`, `:1792-1848`, `:1893-1924`, Hook `:420-502` | T11-Step 6 zieht die Anker mit (ohne Inhaltsdebatte) |
| **F-4** (neu aus diesem Plan) | `docs(spec): #1181 spec cites the dead Bash→code_execution mapper for Gemini` | `docs`, `P3` | Spec §3.3 verweist auf `scripts/lib/provider_transform.py:854-870`; diese Funktion wird im Render-Pfad **nie aufgerufen** (einziger Treffer ist die Definition; `config/provider-capabilities.yaml:290` führt sie selbst als offene Inkonsistenz). Der lebende Pfad ist `config/ai-providers.yaml:230-251` (`tools: filter`, `tool-name-map: {Bash: run_command}`); `code_execution` erscheint nur als `bash_tool_name` (`:203`, Enforcement-Seite). | **Spec-Text mit Rev. 1.1 korrigiert** (§3.3 + AC-2); K-4 + `test_gemini_grant_maps_to_run_command` (T8) verhindern einen roten Test; das Ticket bleibt für den toten Code |
| **F-5** (neu aus dem Review 2026-11-09) | `bug(hooks): PreToolUse payload carries agent_id but no agent name — command-level scoping for granted roles is not enforceable` | `bug`, `hooks`, `security`, `P3` | Der Guard liest die Rolle ausschließlich aus dem modell-geschriebenen Sentinel (`orchestrator-guard-impl.sh:326-350`); das Payload liefert nur `agent_id` (`:262-269`). Jede rollengebundene Kommando-Grenze ist damit für Kommandos **ohne** Sentinel wirkungslos — genau der Injection-Pfad. | T16 härten den wohlgeformten Pfad; die Grenze wird in T5/T11 ausdrücklich benannt (kein Boundary-Versprechen). Kein Blocker für #1181, weil die Ack-Pflicht (T1) den Grant als Voll-Shell-Grant kontraktiert |

## 14. Offene Entscheidungen (OQ)

| ID | Frage | Empfehlung des Plans | Blockadewirkung |
|---|---|---|---|
| **OQ-1** | Soll `authority_overrides` in v1 auch `delegate`/`notify`/`none` akzeptieren (Entzug)? | **Nein.** Nur `direct` (Schema-Enum); Entzug über `roles:` und über Entfernen des Keys. Ein Entzugs-Enum wäre ein zweiter, ungeprüfter Pfad ohne AC — und würde die K-5-Reason „grant withdrawn" ununterscheidbar machen. | **Blockiert nichts**: v1-Enum ist `["direct"]`; eine spätere Erweiterung ist additiv (Schema + `_KEYS` + Tests). |
| **OQ-2** | Gibt es eine kommando-genaue Bash-Permission (nur `git add`/`git commit`)? | **Nein, nicht belegt.** `provider_transform.py:895-920` mappt Skalare, v2 nutzt `resource: "*"` (`:960-972`). Doku sagt daher „voller Bash, hook-begrenzt". Ein Spike ist ein eigenes Ticket, kein Task hier. | **Blockiert nichts** in v1; blockiert jede Doku-Aussage „nur `git`" — die entfällt (T11). |
| **OQ-3** | Ist der Persona-Konflikt (`documenter` „implementiert nichts" + `Bash`) akzeptabel? | **Ja, mit expliziter Grant-Zeile** (T5) und Doku-Absatz (T11); **keine** Persona-Änderung an `agents/1-generic/documenter.md` (Submodul-Schutz + Byte-Golden für Nicht-Grant-Rollen). | **Blockiert T5/T11-Formulierung**, nicht die Implementierung — ohne Entscheid bleibt die Grant-Zeile die konservative Variante. |
| **OQ-4** | Soll die Schrumpf-Warnung unter `--check`/`--validate` ein ERROR (CI-Gate) sein? | **Nein, WARN.** Sonst bricht jedes Upgrade die CI (und #1142 arbeitet an derselben Exit-Code-Politik). T14-Step 3 pinnt `--check` rc 0. | **Blockiert nichts**; eine spätere Verschärfung wäre ein eigener Task mit #1142. |
| **OQ-5** (aus Spec) | Gilt der Grant auch für `suggest`? | **Nein** — `suggest` ist authority-agnostisch propose-only (`auto_commit.py:383-391`); `resolve_commit_grant` liefert `(derived, False)` (T6). | Keine. |
| **OQ-6** (aus Spec) | Ist ein Grant auf einem hook-losen Provider in einem **gemischten** Provider-Set ein Fehler? | **Nein** (K-9/Spec §4.3): ERROR nur, wenn der Grant **nirgends** durchsetzbar ist (Guard aus oder ausschließlich hook-lose Provider); im gemischten Set bleibt es bei der WARN je Provider. | Blockiert T2-Abgrenzung; Empfehlung ist spec-konform. |
| **OQ-P1** (Plan) | Braucht `resolve_commit_grant` wirklich `agent_meta_root` (K-1)? | **Erledigt:** Signatur steht so in Spec Rev. 1.1 (§4.3); T6 implementiert sie. Keine offene Frage mehr. | Keine. |
| **OQ-P2** (Plan) | Ist „Rolle nicht in `roles:`" ein `--validate`-ERROR? | **Nein** (K-2): kein Fehler, aber eine INFO-Notice aus `authority_override_notices` (T2). ERROR nur für read-only/unbekannte Templates und für nicht durchsetzbare Grants. | Keine. |
| **OQ-P3** (Plan) | Skalar (`documenter: direct`) oder Objekt mit Ack (K-8)? | **Objekt mit Pflicht-Ack** (Review-Variante b, vollständig durchgezogen). Ein Skalar-Kurzweg wird bewusst nicht akzeptiert — zwei akzeptierte Formen wären zwei Parser und zwei Fehlermeldungen. | Blockiert nichts; Schema/Tests in T1/T2. |

---

## 15. Review-Auflösung (2026-11-09)

| Befund-ID | Änderung im Plan | Stelle |
|---|---|---|
| **RVW-1181-01** (BLOCKER) | Neues Modul `hook_state.py` + T15 (ein Prädikat für die effektive Guard-Aktivierung, `sync_hooks` darauf umgestellt); `resolve_commit_grant` bekommt `guard_enabled` (T6); `authority_override_violations` meldet „nicht durchsetzbar" (T2); Sync-Test mit `hooks.orchestrator-guard.enabled: false` (T8), Szenario-Assert (f) (T12), Scratch-Schritt (T13) | §2 K-9/K-11, §3a, §4, §5 (M1/M3), T2, T6, T8, T12, T13, T15, §7.0/§7.1 |
| **RVW-1181-02** (MAJOR) | Variante **(b)** durchgezogen: Objektform mit Pflichtfeld `acknowledge_full_shell: true` (K-8), Schema (T1), Normalisierung + Violation (T2), Fail-Safe (T4), Grant-Zeile benennt die Voll-Shell-Ausweitung (T5), Doku (T11). Zusätzlich Härtung als T16 (Sentinel nur für `git add`/`commit`, `all_git`-Feld). Test `curl …` mit Grant-Sentinel ⇒ rc 2 (T16) | §2 K-8/K-11, §3, §4, T1, T2, T4, T5, T11, T16, §8, §10 (R1/R3c), §11 (N-2/N-3) |
| **RVW-1181-03** (MAJOR) | Neues `--validate`-Finding in T2 (`grant not enforced (…)`, zwei Ursachen), Abgrenzung ERROR/WARN über OQ-6; Tests für hook-losen Provider und deaktivierten Guard | §2 K-9, T2-Step 1/3/6, §7.4, §11 (N-1/N-4), §14 (OQ-6) |
| **RVW-1181-04** (MAJOR) | K-5 ersetzt: Gründe disjunkt, Reihenfolge `grant withdrawn → role removed → gate-dropped → no Bash`, `no Bash` nur für Rollen in `roles:`; T9-Fixture entsprechend korrigiert (copyeditor/documenter/planner **in** `roles:`, product-manager nicht) | §2 K-5, T9-Step 1/3, §7.4, §8 |
| **RVW-1181-05** (MINOR) | K-4 belegt jetzt den toten Mapper zusätzlich über `provider-capabilities.yaml:290`; Gemini-Anker `ai-providers.yaml:230-251` (`run_command`); Spec Rev. 1.1 korrigiert; AC-2-Traceability nennt `run_command` | §2 K-4, §4 (kein `provider_transform.py`-Change), T8, §11 (AC-2), §13 (F-4) |
| **RVW-1181-06** (MINOR) | Baseline-Zahlen aus echtem Lauf: 75 gesamt, `test_auto_commit_lib.py` **17**, `test_auto_commit_violations.py` **18** (Summe vorher fälschlich 69); Gates auf `0 failed` + benannte Tests umgestellt, T1/T5-Verweise korrigiert (30 statt 29 Bestand, 20 statt 23 Render-Tests) | §5, §8, T1-Step 4, T5-Step 3, T14-Step 1 |
| **Signatur-WARN** | K-1 + Spec §4.3: `resolve_commit_grant(..., agent_meta_root, *, guard_enabled)`; `authority_override_violations(config, agent_meta_root, provider_config=None)`; `resolve_auto_commit_config` normalisiert | §2 K-1, §7.1, T2, T6 |
| **T14-WARN** | T14 trägt jetzt `Files: — (Verifikation)` und hängt von T15/T16 ab; kein Datei-Ownership-Konflikt mehr | §4, T14 |
| **NIT `ALLOWLIST_VERSION`** | K-10: Versionssprung als bewusster Default-Diff für **jeden** Consumer, auch ohne Grant; Test in T9, `CHANGELOG` „Changed“ in T11, Migration §9, Risiko R11 | §2 K-10, §3, §7.3, T9, T11, §9, §10 (R11) |
| **NIT `active_roles`** | Parameter entfernt aus `authority_override_violations`, dafür `authority_override_notices(config, active_roles)` (INFO bei inaktiver Rolle) — T2 implementiert und testet beides | §2 K-2, T2-Step 1/4, §7.1, §7.4 |
| **Querschnitt** | Kanonische Reihenfolge und gemeinsame Konfliktmatrix (inkl. `agent_sync.py`-Rollen-Schleife `:1457-1468`/`_finalize_agent_content`, `sync_pipeline.py:1893-1924`, `variables.py`, `standalone.py`, `registry.md`, alle drei `project.yaml.example`, Hook vs. #1151); Szenario-IDs `94` / `95–98`; `docs/issue-labels.md` → #1186 | Header, §3a, §12, T12-Step 4 |
| **RVW2-1181-01** (MAJOR) | Opencode aus dem positiven Render-Vertrag entfernt (K-12): real nur `bash: deny`/`shell: deny` + WARN; die T8-Tests `test_opencode_v1_…_bash_allow_when_granted`/`test_opencode_v2_…_shell_allow_when_granted` sind gestrichen und durch `test_render_bash_on_synthetic_hook_capable_fixture` ersetzt; M3-Gate und §8-Tabelle angepasst. | §1 (Nr. 3), §2 K-12, §5 (M3), §8, T8-Step 1/5, §11 (AC-2) |
| **RVW2-1181-02** (MAJOR) | `agents/`-Nachweis commit-fest (K-16): M1-Gate und T14-Step 4 nutzen `git diff --name-only aaed14c2..HEAD -- agents/`; §11 AC-1 entsprechend. | §2 K-16, §5 (M1), T14-Step 4, §11 (AC-1) |
| **RVW2-1181-03** (MAJOR) | T7 prüft vor dem Render `authority_override_violations(config, agent_meta_root)`; der Fail-Safe-Zweig setzt `mode: off`, `authority_overrides: {}` und `INVALID_CONFIG_MARKER`. Test `test_core_variables_grant_without_ack_triggers_fail_safe`. T7 hängt jetzt von T2 ab. | §2 K-13, §4 (T7), T7-Step 1/2 |
| **RVW2-1181-04** (MINOR) | Mapping-Guard in `effective_commit_authority` (K-14): `isinstance(authority_overrides, Mapping)` vor `.get`; `authority_overrides=["x"]` liefert den abgeleiteten Wert statt `AttributeError`. | §2 K-14, §7.1 (Docstring), T3-Step 2 |
| **RVW2-1181-05** (MINOR) | `authority_override_notices` erhält die effektive aktive Menge (raw ∩ `active_set.has`); neuer Test `test_grant_notice_for_gate_dropped_role`. | §2 K-15, T2-Step 1/6 |
| **RVW2-X-01** (MAJOR, Querschnitt) | §3a-Matrix auf die verbindliche Zielmatrix gebracht: `agent_sync.py` #1187/#1188/#1181; `sync_pipeline.py` #1186/#1181 (#1187 nur bei echtem Task); `variables.py`/`standalone.py` #1187; `registry.md` #1181/#1187/#1186; beide `project.yaml.example` #1187/#1186/#1188/#1181; `docs/issue-labels.md` und `.meta-config/issue-labels-state.json` #1188 erzeugt, #1186 klassifiziert (K1: `unmanaged`, nicht `project-state`). | Header, §3a |

### 15.1 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Status bleibt `DRAFT`.

| Befund | Änderung im Plan | Stelle |
|---|---|---|
| **K1** (BLOCKER) | State-Datei ist `unmanaged`, nicht `project-state` | §3a (Matrix-Zeile), RVW2-X-01-Zeile |
| **K2** | **Nicht betroffen**: kein Label-Separator | geprüft: §3a |
| **K3** | **Nicht betroffen**: keine Preset-Präzedenz | geprüft: §2 K-17 |
| **K4** | **Nicht betroffen**: keine `taxonomyAxis` | geprüft: T1 |
| **K5** (MINOR) | Provider-/Guard-Gate ist **Wirkbedingung** nach dem Grant, keine Präzedenzstufe 7; T6/T8 prüfen es weiterhin nach der Auflösung | **§2 K-17** |
| **K6** | **Nicht betroffen**: Schema-Sketch ohne `$defs` | geprüft: T1 |
| **K7** (NIT) | `acknowledge-full-shell` → **`acknowledge_full_shell`** in allen Schema-, Test-, Doku-, Beispiel- und Meldungsstellen; Stilsatz dokumentiert | **§2 K-18**, T1, T2, T5, T10, T11, §7, §11 (N-2) |
| **K8** | Schema **und** `_KEYS` im selben PR + Mengengleichheits-Test (`schema.properties.auto_commit.properties == _KEYS`) als DoD-Nachweis | **§2 K-19**, **T1-Step 3**, **T14-Step 7** |

---

## Self-Review

- **Rollen-Mapping:** T1–T7, T9, T10, T12, T15 → `developer`/`senior-developer`; T8, T16 →
  `senior-developer`; T11 → `technical-writer`; T13 → `senior-developer`; T14 → `validator`.
  Jeder Task hat genau eine Rolle.
- **Messbarkeit:** Jeder Task endet mit einem ausführbaren Befehl + erwartetem Ergebnis
  (`0 failed`, rc, exakte Log-Zeile). Keine „funktioniert korrekt"-Kriterien; Sollzahlen sind
  durch `0 failed` + benannte Tests abgesichert (RVW-1181-06).
- **Datei-Ownership:** Innerhalb eines Meilensteins überlappt keine Datei zwischen parallel
  denkbaren Tasks (M1: Schema/`auto_commit.py`/`hook_state.py`/`hooks.py` → T1→T15→T2 sequentiell;
  M2: `auto_commit.py` sequentiell T3→T4→T5; M3: `auto_commit.py`/`config.py`/`agent_sync.py`
  getrennt; M4: `sync_pipeline.py` (T9) vor der Hook-Datei (T16); M5: `admin-ui.html` vs. Doku).
  Sequenzialisierung ist damit auch ohne Barrieren-Logik sicher.
- **Anker:** Die Review-Anker wurden erneut geprüft: `providers.py:700-709`,
  `hooks.py:621-626`/`:447-456`, Schema `:736-752`, `orchestrator-guard-impl.sh:262-269`/`:326-350`/
  `:511-521`/`:1282-1326`/`:1336`/`:1535`, `ai-providers.yaml:203`/`:230-251`,
  `provider_transform.py:854-870` (toter Mapper), `agent_sync.py:92-123`/`:935`/`:1010`/`:1457-1468`,
  `sync_pipeline.py:1893-1924`, `cli_commands.py:1432-1439`/`:1462`.
- **Kein Platzhalter:** Kein Task enthält TBD/„analog oben"; jede Log-Zeichenkette, jeder Testname
  und jede Signatur ist ausgeschrieben, jede Tabelle ist vollständig gefüllt.
- **Rollback:** drei Ebenen (Key entfernen / `mode: off` / Code-Revert), alle ohne Datenverlust,
  Allowlist v1 bleibt lesbar; `hook_state.py` ist additiv und kann mit dem Hook-Revert bleiben.
- **Grenze:** Die Spec ist `DRAFT`; dieser Plan ist ebenfalls `DRAFT` und darf nicht vor
  `Status: APPROVED` der Spec ausgeführt werden (Master-Rule `spec-plan-workflow`).

**Trace-Anker:** `SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09` · Issue #1181 ·
`pipeline_stages: implement: 1`.
