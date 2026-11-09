---
spec-id: SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09
title: Projektseitiger Commit-Authority-Grant für Edit-only-Rollen
status: DRAFT
revision: "1.4"
review: "2026-11-09 — RVW-1181-01 … -06 + RVW2-1181-01 … -05 + RVW2-X-01 (§12); Szenario-Konflikte K1–K8 (§12.1); Nutzerentscheidungen D16–D23 (§13)"
klasse: L (Bounded, mit Review-Loop) — Begründung im Kopfblock unten
issue: "#1181"
datum: 2026-11-09
autor: concept-specifier (Subagent, Auftrag via orchestrator)
related-spec: SPEC-am-767-auto-commit-authority
quellen: >
  .tmp/issue-dump/issue-1181.json (maßgeblich),
  .tmp/issue-dump/issue-1186.json, -1187.json, -1188.json (Konfliktflächen),
  .tmp/issue-dump/issue-1142.json, -1151.json, -1172.json (Backlog),
  .tmp/issue-dump/baseline-validate.txt, baseline-check.txt;
  Review 2026-11-09 (RVW-1181-01 … -06); Code-Belege mit Datei:Zeile unten.
---

# Projektseitiger Commit-Authority-Grant für Edit-only-Rollen — Spec

> **Status: DRAFT** — kein `APPROVED`. Der Approval-Marker wird ausschließlich vom Nutzer bzw.
> `concept-reviewer` gesetzt, nie vom Autor. Diese Datei enthält Interface-Contracts und
> Akzeptanzkriterien, **keine** Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09`.
>
> **Issue:** [#1181 — feat: supported way to grant commit authority to Edit-only roles](https://github.com/Popoboxxo/agent-meta/issues/1181)
> **Klasse: L** (Bounded, Review-Loop) — ein öffentlicher Config-Contract plus eine Schema-Änderung
> an einem `additionalProperties: false`-Block, verteilt auf zehn Produktionsdateien (davon zwei
> neu); kein neuer Subsystem-Schnitt, keine neue Datenhaltung. Das Architectural-Kriterium
> „öffentlicher Contract + Schema“ ist berührt, daher der `concept-reviewer`-Loop.
> **Revision:** 1.4 (2026-11-09) — die offenen Fragen (OQ-1…OQ-6, OQ-P2, OQ-P3) sind
> **entschieden** (D16–D23, §13): Persona-Konflikt akzeptiert **ohne** Persona-Änderung (D16),
> Grant bleibt reine Eskalation ohne Revoke-Wert (D17), voller `Bash` mit Hook-Härtung und
> ausdrücklich ehrlicher Doku inkl. Attributionslücke **#1210** (D18), Schrumpf-Warnung bleibt
> WARN ohne CI-Gate (D19), kein Grant unter `suggest` (D20), gemischtes Provider-Set = WARN je
> Provider und ERROR nur bei Nirgends-Durchsetzbarkeit (D21), Rolle nicht in `roles:` = INFO
> (D22), ausschließlich Objektform mit Pflicht-Ack (D23).
> 1.3 (2026-11-09) — Szenario-Konflikte K1–K8: `acknowledge_full_shell` (snake_case
> im `auto_commit`-Block, K7), Provider-/Guard-Gate als Wirkbedingung statt Präzedenzstufe 7 (K5),
> `_KEYS`-Mengengleichheit im selben PR (K8), `unmanaged` statt `project-state` (K1); Details in §12.1.
> 1.2 (2026-11-09) — zweite Korrekturrunde: RVW2-1181-01…05 und RVW2-X-01
> (Render-Vertrag Opencode, Commit-feste `agents/`-Prüfung, Fail-Safe in `config.py`,
> Mapping-Guard, effektive aktive Menge, Zielmatrix); Details in §12.
> 1.1 (2026-11-09) — Review-Auflösung RVW-1181-01…06; 1.0 (2026-11-09), Erstentwurf.

## 1. Problem & Motivation

### 1.1 Ausgangslage

`auto_commit.mode` und seine Trigger sind projektseitig konfigurierbar
(`config/project-config.schema.json:1495-1545`), die **Commit-Authority** einer Rolle ist es nicht.
`eligible_roles` — die Liste, die den Guard-Hook-Sentinel autorisiert — wird ausschließlich aus dem
`tools:`-Frontmatter des 1-generic-Templates abgeleitet und ist absichtlich Bash-only
(`scripts/lib/auto_commit.py:127-153`). Eine Rolle ohne `Bash` bekommt in jedem generierten Agenten
`bash: deny` und kann `git add`/`git commit` nicht ausführen; sie in die Allowlist aufzunehmen ist
still wirkungslos.

### 1.2 Stille Regression beta.1 → beta.8

- **Verifiziert:** Commit `b5bfa2cf` existiert (GitHub-API, committet 2026-10-04T18:27:46Z) mit der
  Message `fix: derive auto-commit authority from real permissions (#874)` und nennt „keep
  eligible_roles direct-only“.
- **Verifiziert:** Release-Reihenfolge — `2.0.0-beta.1` (2026-10-03, `CHANGELOG.md:1512`) liegt
  **vor** dem Commit, `2.0.0-beta.2` (2026-10-20, `CHANGELOG.md:786`) danach; die Bash-Anforderung ist
  damit erstmals in beta.2 ausgeliefert.
- **Verifiziert im Code:** die Bash-Bedingung steht heute in
  `scripts/lib/auto_commit.py:139-140`; `is_role_eligible()` verlangt `direct`
  (`:146-153`), der Modul-Docstring begründet das direkt-only (`:17-18`).
- **Laut Issue (nicht im Repo verifizierbar, Consumer-spezifisch):** beim Upgrade beta.1 → beta.8
  verschwanden 13 Rolleneinträge aus `.meta-config/auto-commit-allowlist.json` (24 verblieben), ohne
  jede Log-Zeile. Der `log.warn()`-Aufruf der Stage feuert nur für Schema-Verstöße
  (`scripts/lib/sync_pipeline.py:1912-1915`), nicht für das Schrumpfen der Liste.

### 1.3 Warum das ein Feature ist, kein Bugfix

Der Fix aus #874 hat die Über-Grantierung korrekt entfernt, aber die Gegenrichtung fehlt: es gibt
keinen unterstützten Weg, einer Edit-only-Rolle Commit-Authority **bewusst** zu geben, ohne
meta-eigene Dateien unter `agents/` zu editieren (was die `submodule-protection`-Regel verletzt und
beim Upgrade kollidiert).

### 1.4 Betroffene Rollen (eigene Messung, nicht nur „laut Issue“)

Gegen HEAD `aaed14c2` (`v2.0.0-beta.8`), 98 deploybare Templates in `agents/1-generic/`
(101 `.md`-Dateien minus `_README.md`, `_reference-agent.md`, `_wf-orchestrator-reference.md`),
`tools:`-Blöcke geparst (2-Leerzeichen- und 0-Leerzeichen-Einrückung), Regel aus
`scripts/lib/auto_commit.py:127-143` angewendet:

- **21 Templates** führen `Edit` und/oder `Write` **ohne** `Bash` — exakt die im Issue genannte
  Liste: `concept-architect`, `concept-reviewer`, `concept-specifier`, `copyeditor`, `documenter`,
  `ideation`, `knowledge-curator`, `knowledge-gardener`, `knowledge-indexer`, `knowledge-ingestor`,
  `knowledge-querier`, `orchestrator`, `planner`, `product-manager`, `proofreader`, `requirements`,
  `risk-based-audit-planner`, `se-integration-and-test-manager`, `se-interface-mgr`, `se-termination`,
  `technical-writer`.
- Aufteilung nach `role_commit_authority()`: **2 × `delegate`** (spawn-fähig via `Agent`:
  `orchestrator` — `agents/1-generic/orchestrator.md:7-12`; `knowledge-curator` —
  `agents/1-generic/knowledge-curator.md:8-9`), **19 × `notify`**.
- Beleg für die Render-Wirkung: `agents/1-generic/documenter.md:11-17` deklariert
  `Read, Write, Edit, Glob, Grep, TodoWrite`; die Opencode-Abbildung setzt daraus `bash: deny`
  (`scripts/lib/provider_transform.py:895-918` plus Deny-Liste
  `config/provider-tools.yaml:58-61`), die v2-Abbildung schließt `shell` explizit
  (`provider_transform.py:930-972`).

## 2. Ist-Zustand (mit Belegen)

### 2.1 Bash-Zwang in der Authority-Ableitung

| Fakt | Beleg |
|---|---|
| `_ELIGIBLE_TOOLS = {"Edit", "Write"}` | `scripts/lib/auto_commit.py:28` |
| `direct` nur bei `Bash` ∧ Write | `scripts/lib/auto_commit.py:137-143` |
| `eligible_roles` ist direct-only | `scripts/lib/auto_commit.py:146-153`, `:17-18` |
| Ableitung nur aus `agents/1-generic/<role>.md`, Plattform-Overrides bewusst ignoriert | `scripts/lib/auto_commit.py:77-87` |
| `eligible_roles` = Filter der übergebenen Rollenliste über `is_role_eligible` | `scripts/lib/auto_commit.py:283-287` |
| Provider-Abbildung erzeugt `bash: deny`, wenn `Bash` fehlt (v1) bzw. `shell: deny` (v2) | `scripts/lib/provider_transform.py:895-918`, `:930-972`; Deny-Quelle `config/provider-tools.yaml:58-61` |
| Guard-Hook prüft `mode ∈ {auto, custom}` und dann `eligible_roles` | `hooks/1-generic/orchestrator-guard-impl.sh:448-478` |
| Der Sentinel gilt nur für `add` und nicht-amendierendes `commit` (narrow scope) | `hooks/1-generic/orchestrator-guard-impl.sh:511-521`, Gate `:1535` |
| Der Hook begrenzt **ausschließlich Git-Mutationen**; jedes andere Bash-Kommando eines Subagenten passiert | `hooks/1-generic/orchestrator-guard-impl.sh:1527-1547` |
| Der Hook kennt die Rolle **nur** aus dem Sentinel; das Payload trägt sonst nur `agent_id` | `hooks/1-generic/orchestrator-guard-impl.sh:262-269`, Sentinel-Parse `:326-350` |
| Die Hook-Aktivierung ist projektseitig abschaltbar (`hooks.<stem>.enabled`), Default aus `# enabled_by_default: true` | `hooks/1-generic/orchestrator-guard.sh:7`; Schema `config/project-config.schema.json:736-752`; Auswertung `scripts/lib/hooks.py:621-626` + `_strict_enabled` `:447-456` |

### 2.2 Allowlist wird vollständig überschrieben, ohne Schrumpf-Vergleich

- Rollenquelle ist die **rohe** Projekt-Allowlist `ActiveSet.raw_roles`, nicht die berechnete
  ActiveSet-Menge (`scripts/lib/sync_pipeline.py:1908`); ohne `roles:`-Key ist die Liste leer.
- Danach wird das Ergebnis zusätzlich gegen `active_set.has()` geschnitten
  (`scripts/lib/sync_pipeline.py:1917-1919`; `scripts/lib/active_set.py:66-67`).
- Geschrieben wird mit `write_atomic` über die **ganze** Datei
  (`scripts/lib/sync_pipeline.py:1921-1924`) — der vorherige Stand wird nicht gelesen, ein
  Schrumpfen ist damit nicht beobachtbar. Gewarnt wird ausschließlich bei Schema-Verstößen
  (`:1909-1915`).

### 2.3 Kein projektseitiger Override für Tools/Authority

- `permission-mode-overrides` setzt ausschließlich Claude's `permissionMode`
  (`scripts/lib/roles.py:565-577`; Schema `config/project-config.schema.json:518-530`) — nicht die
  Tool-Liste, nicht die Allowlist, nicht die Permission-Map.
- Es gibt **keinen** Key `tools-overrides`, `commit-authority-overrides` oder
  `authority_overrides` — weder im Schema (Grep über `config/project-config.schema.json`,
  `scripts/lib/roles.py`, `scripts/lib/provider_transform.py`: kein Treffer) noch in
  `.meta-config/project.yaml` (Grep: kein Treffer).
- Der einzige verbleibende Hebel ist das Editieren von `agents/3-project/<role>.md` bzw. des
  Submoduls — genau der Weg, den `submodule-protection` verbietet.

### 2.4 Admin-UI verwirft unbekannte `auto_commit`-Keys beim Speichern

`viewProjectAutoCommit` klont den Block (`docs/ui/admin-ui.html:7650`), baut beim Save aber ein
**neues** Objekt `const out = { mode }; …` (`:7753-7760`) und sendet nur dieses
(`saveProjectSection("auto_commit", out, …)`, `:7761`). Ein neuer Key, der nicht in dieses `out`
aufgenommen wird, wird bei jedem UI-Speichern still gelöscht (siehe §8.2, Finding F-2).

### 2.5 Baseline

`baseline-validate.txt`: `consistency-check` grün, `EXIT=0`, ein WARN
(`repo-containment.no-hook-support` für Opencode). `baseline-check.txt:1-6` listet die fünf
erwarteten Vorab-Warnungen (u. a. `active-set.gate-dropped` und `mcp.secret-empty`), ohne
`auto_commit`-Befund — der Block ist im Selbst-Hosting also schema-gültig. Für diese Spec relevant:

- Opencode ist hook-los (`config/provider-capabilities.yaml:179`), Claude und Gemini sind
  hook-fähig (`:121`, `:237`) — die Grant-Durchsetzung ist damit provider-abhängig (§3.3).
- Das Selbst-Hosting-Projekt setzt `hooks: {dod-push-check, graphify-read-guard,
  graphify-search-guard}` (`.meta-config/project.yaml:155-161`) und **keinen** Eintrag für
  `orchestrator-guard`; der Guard ist dort also über `enabled_by_default: true` aktiv. Ein Projekt
  mit `hooks.orchestrator-guard.enabled: false` ist der Gegenfall aus §3.3 Bedingung 5.

## 3. Soll-Verhalten

### 3.1 Neuer Config-Key

```yaml
auto_commit:
  mode: auto                       # unverändert: off|suggest|auto|custom
  triggers: [task-boundary, file-count-threshold]
  authority_overrides:             # NEU (Issue #1181), Default: {}
    documenter:                    # Referenzfall aus AC-1
      authority: direct            # v1: einziger zulässiger Wert
      acknowledge_full_shell: true # PFLICHT (RVW-1181-02): bestätigt die volle Shell-Ausweitung
    planner:
      authority: direct
      acknowledge_full_shell: true
```

- Der Key lebt **innerhalb** von `auto_commit`, damit Mode-Gate, Trigger und Grant denselben
  Lebenszyklus haben und der bestehende Fail-Safe-Mechanismus (#1091) unverändert greift.
- Der Wert je Rolle ist ein **Objekt**, kein Skalar. `authority` ist in v1 auf `direct` beschränkt
  (Eskalation; `delegate`/`notify` sind bereits automatisch ableitbar, eine Rücknahme läuft
  ausschließlich über die `roles:`-Allowlist oder das Entfernen des Override-Keys — D17).
- `acknowledge_full_shell` ist **Pflicht und muss `true` sein**. Begründung (RVW-1181-02): der Grant
  ist eine volle `Bash`-Ausweitung; der Guard-Hook kann nur Sentinel-tragende Kommandos einer Rolle
  zuordnen (§3.3.1). Ohne explizite Bestätigung wäre die Ausweitung eine unbeabsichtigte
  Nebenwirkung eines Feldes, das „Commit-Authority“ heißt.
- Ein Grant ist **opt-in pro Rolle** und niemals Default. Ohne den Key ist der Render
  byte-identisch zu heute.

> **DECIDED 2026-11-09 (D23 — OQ-P3): nur Objektform mit Pflicht-Ack.** Der Wert je Rolle ist
> **immer** `{authority: direct, acknowledge_full_shell: true}`. Die Skalar-Kurzform
> (`documenter: direct`) wird **nicht** akzeptiert — sie ist ein Schema- und Validierungsfehler
> und erzeugt **keinen** Grant. Ein fehlendes oder falsches Ack (`false`, `"true"`, fehlend) ist
> ebenfalls eine Violation ohne Grant (§4.1, §4.3). Zwei akzeptierte Formen wären zwei Parser und
> zwei Fehlermeldungen; es gibt genau einen.

> **DECIDED 2026-11-09 (D17 — OQ-1): nur geben, kein Revoke.** `authority` hat in v1 genau einen
> zulässigen Wert: `direct`. Es gibt **keinen** Revoke-Wert (`notify`/`delegate`/`none`) und
> keinen Grant, der eine bestehende Authority zurücknimmt. Entzug läuft ausschließlich über
> (a) Entfernen der Rolle aus `roles:` oder (b) Entfernen des Override-Keys; die
> Schrumpf-Begründung `grant withdrawn` bleibt an (a) gebunden (§3.5).

**Namensstil innerhalb der Welle (Review-Auflösung K7).** Neue **Top-Level**-Sektionen der
Config-Welle sind kebab-case (`project-context-injection`, `artifact-locations`,
`issue-conventions`). **Innerhalb** einer bestehenden Sektion gilt deren Stil weiter: `auto_commit`
ist snake_case (`file_count_threshold`, `custom_script`, `secret_scan`), deshalb heißt der neue
verschachtelte Key **`acknowledge_full_shell`** (nicht `acknowledge-full-shell`). Die Regel lautet:
Der Stil der *umschließenden Sektion* gewinnt; ein neuer Top-Level-Key bringt seinen eigenen
(kebab-case) Stil mit.

### 3.2 Auflösung der effektiven Authority

Neue reine Funktion in `scripts/lib/auto_commit.py`:

```python
def effective_commit_authority(
    role: str,
    agent_meta_root: Path,
    platform: str | None = None,
    authority_overrides: Mapping[str, str] | None = None,
) -> str:
    """Wie role_commit_authority(), aber ein gültiger Grant eskaliert
    delegate|notify -> direct. Alles andere bleibt die abgeleitete Klasse."""
```

Regeln:

1. `derived = role_commit_authority(role, agent_meta_root, platform)` — unverändert.
2. `wanted = authority_overrides.get(role) if isinstance(authority_overrides, Mapping) else None`
   — hier bereits die **normalisierte** Map `<role> -> "direct"` (Regel 6), nicht die rohe
   Config-Form. Ein Nicht-Mapping (z. B. eine Liste) wird wie `None` behandelt
   (RVW2-1181-04), damit die Funktion ihren Vertrag „wirft nie" auch bei einem
   aufruferseitigen Typfehler hält.
3. `wanted == "direct"` und `derived in {"delegate", "notify"}` → `direct`.
4. Sonst `derived` (kein Fehler, kein stilles Grant): `derived == "direct"` ist ein No-op,
   `derived == "none"` wird schon bei der Validierung abgewiesen (§4.3).
5. Die Funktion wirft nie; ein Nicht-Mapping wird wie „kein Grant" behandelt
   (RVW2-1181-04). Validierung ist Sache von `authority_override_violations` /
   `authority_override_notices`.
6. **Normalisierung (eine Stelle, §4.3):** `authority_overrides` wird genau einmal von
   `{role: {authority: "direct", acknowledge_full_shell: true}}` nach `{role: "direct"}`
   überführt. Nur Rollen mit `authority == "direct"` **und** `acknowledge_full_shell is true`
   werden überführt; jede andere Form erzeugt eine Violation und niemals einen Grant. Es gibt
   keinen zweiten Parser und keinen Skalar-Kurzweg. Ein `authority`-Wert außer `direct` ist
   deshalb **kein** Revoke, sondern ein Konfigurationsfehler (D17).

### 3.3 Wirkung auf den generierten Agenten (Render-Vertrag)

Ein Grant wirkt **nur**, wenn alle fünf Bedingungen erfüllt sind:

1. `auto_commit.mode ∈ {auto, custom}` (bei `off`/`suggest` gibt es nichts zu committen bzw. nur
   Vorschläge — `scripts/lib/auto_commit.py:350-352`, `:383-391`). **D20:** `suggest` ist
   ausdrücklich **kein** Grant-Modus.
2. Die Rolle steht normalisiert in `authority_overrides` mit `direct` und ihre abgeleitete Klasse
   ist `delegate` oder `notify`.
3. Die Rolle ist aktiv (`roles:`-Allowlist **und** ActiveSet, §4.2).
4. Der Provider hat einen verifizierten, gespiegelten Hook:
   `provider_hooks_supported(pc)` (`scripts/lib/providers.py:700-709`).
5. **Der Guard-Hook ist effektiv aktiv** (RVW-1181-01): `resolve_hook_enabled(config["hooks"],
   "orchestrator-guard", enabled_by_default=True)` liefert `(True, False)` — dasselbe Prädikat, das
   `sync_hooks` für die Registrierung verwendet (`scripts/lib/hooks.py:621-626`, `_strict_enabled`
   `:447-456`; Default `true` aus `hooks/1-generic/orchestrator-guard.sh:7`). Ein Projekt mit
   `hooks.orchestrator-guard.enabled: false` bekommt **kein** `Bash` gerendert (fail closed,
   §4.3/§4.6).

> **DECIDED 2026-11-09 (D20 — OQ-5): der Grant wirkt nicht in `suggest`.** `resolve_commit_grant`
> liefert für `mode: suggest` unbedingt `(derived, False)` — kein `Bash`-Render, kein
> Grant-Zusatz im Block, kein Hook-Sentinel (der Hook verlangt `auto`/`custom`,
> `orchestrator-guard-impl.sh:459-464`). Der Grant bleibt in `eligible_roles` und im
> Allowlist-Artefakt sichtbar (Capability, nicht Mode, §4.4), hat aber keine Render-Wirkung.
> `suggest` ist propose-only und authority-agnostisch.

Bei erfüllten Bedingungen gilt pro Provider:

| Provider | Render-Wirkung | Beleg |
|---|---|---|
| Claude | `tools:` des generierten Agenten erhält `Bash`; der Guard-Hook begrenzt zur Laufzeit Sentinel-tragende Kommandos auf `add` + nicht-amendierendes `commit` (§3.3.1) | `scripts/lib/frontmatter.py:184-209`; Hook `:511-521`, `:1535` |
| Gemini | `Bash` → `run_command` über `agent-transform.tool-name-map` (datengetrieben); `tool-name-map` ist der **lebende** Pfad | `config/ai-providers.yaml:230-251` (`tools: filter`, `tool-name-map.Bash: run_command` `:250`) |
| Hook-lose Provider (Continue, Copilot, Mammouth, Codex, ZCode, KimiCode, **Opencode**) | **keine** Render-Erweiterung; die Rolle behält `notify`/`delegate`-Prosa | `config/provider-capabilities.yaml:179, 304, 365, 434, 489-506, 579, 648`; `provider_hooks_supported` verlangt `hook_protocol ∈ {claude-code-json, antigravity-hooks-json}` (`scripts/lib/providers.py:690, 700-709`) |
| Guard deaktiviert (jeder Provider) | **keine** Render-Erweiterung, zusätzlich WARN + `--validate`-ERROR | `scripts/lib/hooks.py:621-626`; diese Spec §3.3 Bedingung 5, §4.6 |

**Opencode ist kein positiver Render-Fall (RVW2-1181-01):** `config/ai-providers.yaml:274`
setzt `has_hooks: false`, `config/provider-capabilities.yaml:179` `hooks: false`. Eine Zeile
„Opencode v1/v2 ⇒ `bash: allow`/`shell allow`" wäre mit Bedingung 4 unerreichbar; sie ist
deshalb entfernt. Der **einzige reale** Opencode-Fall ist der hook-lose Deny-Pfad:
`bash: deny`/`shell: deny` plus WARN (§4.6). Positive Render-Tests für
`bash: allow`/`shell: allow` dürfen nur gegen einen **synthetischen, hook-fähigen
Capability-Fixture** laufen (Form eines Claude-/Antigravity-Providers), nie gegen die reale
Opencode-Kapabilität (Plan T6/T8).

**Gemini-Korrektur (RVW-1181-05):** `code_execution` ist **nicht** der Render-Pfad.
`_map_claude_tools_to_gemini_tools()` (`scripts/lib/provider_transform.py:854-870`) hat keinen
Aufrufer (Beleg: `config/provider-capabilities.yaml:290` führt den toten Mapper explizit als offene
Inkonsistenz; Repo-Grep findet nur die Definition). `bash_tool_name: code_execution`
(`config/ai-providers.yaml:203`) beschreibt die **Enforcement-/Hook-Seite**, nicht die
Frontmatter-Abbildung. Tests müssen `run_command` asserten (Finding F-4).

Begründung für die Zeile „hook-lose Provider“: ohne Hook wäre ein `direct`-Grant reine Prosa auf
einem Agenten, der `Bash` gar nicht ausführen darf — genau der Widerspruch aus #767
(`docs/specs/767-auto-commit-permission-authority.md:5-30`). Deshalb wird der Grant dort **nicht**
gerendert und stattdessen gewarnt (§4.6). Dasselbe gilt für den deaktivierten Guard: ein
`Bash`-Grant ohne Guard-Gate ist eine unbeschränkte Shell auf einer Edit-only-Rolle und damit
schlechter als kein Grant.

> **DECIDED 2026-11-09 (D21 — OQ-6): gemischtes Provider-Set = WARN je Provider.**
> Die Auflösung ist **per Provider**: auf einem Provider mit verifiziertem Hook **und** aktivem
> Guard wird der Grant gerendert (INFO-Zeile, `hook-enforced: yes`); auf allen anderen Ziel-
> Providern bleibt es bei der abgeleiteten Authority plus WARN je Provider (§4.6). Ein
> `--validate`-**ERROR** entsteht ausschließlich dann, wenn der Grant auf **keinem** Ziel-Provider
> wirken kann (Guard global aus **oder** alle Ziel-Provider ohne verifizierten Hook). Ein
> Zwei-Provider-Projekt (z. B. Claude + Opencode) ist damit **nicht** dauerhaft rot.

Die `eligible_roles`-Liste bleibt davon unberührt provider-agnostisch (Capability, nicht
Enforcement) — konsistent mit dem bestehenden Docstring (`scripts/lib/auto_commit.py:261-263`).

### 3.3.1 Grant-Scope und Durchsetzungsgrenze (RVW-1181-02)

Der Grant rendert **`Bash`, nicht „nur `git`“**. Die Durchsetzung ist dreigeteilt:

1. **Bestehend:** Git-Mutationen eines Sentinel-tragenden Kommandos sind auf `git add` und ein
   nicht-amendierendes `git commit` begrenzt (narrow scope,
   `hooks/1-generic/orchestrator-guard-impl.sh:511-521`, Gate `:1535`).
2. **Neu (Härtung):** Für Rollen, die in der Allowlist unter `authority_overrides` stehen
   (§4.4), akzeptiert der Hook den Sentinel **nur** für ein Kommando, dessen sämtliche Statements
   `git` sind und dessen Mutations-Scope `narrow` ist. Jedes andere Sentinel-tragende Kommando
   endet mit rc 2 und der Meldung
   ``ORCHESTRATOR_GUARD: a granted commit role may only use its sentinel for `git add`/`git commit` (issue #1181).``
   Technisch: der Klassifizierer (`orchestrator-guard-impl.sh:1282-1326`) gibt ein viertes Feld
   `all_git` aus (jedes Statement beginnt mit `git`), die Shell prüft vier Felder statt drei
   (`:1336`) und das neue Gate steht neben dem Mutations-Gate (`:1535`).
3. **Grenze (bleibt bestehen):** Der Hook kann ein Kommando **ohne** Sentinel keiner Rolle
   zuordnen — das PreToolUse-Payload trägt nur ein opakes `agent_id`, keinen Rollennamen
   (`orchestrator-guard-impl.sh:262-269`; Sentinel-Parse `:326-350`). Prompt-Injection schreibt
   keinen Sentinel. Eine kommando-genaue Grant-Begrenzung ist damit **keine** Security-Boundary
   gegen Injection; sie ist Defense-in-Depth für den wohlgeformten Pfad.

Deshalb ist `acknowledge_full_shell: true` Pflicht (§3.1) und der Grant ist im Render-Text, im
`CHANGELOG` und in der Doku ausdrücklich als volle Shell-Ausweitung benannt (§4.5, §7.1).

> **DECIDED 2026-11-09 (D18 — OQ-2): voller `Bash` + Hook-Härtung + ehrliche Doku.**
> Es gibt **keine** kommando-genaue Provider-Permission und keine Zusage „nur `git`". Verbindlich
> sind drei Aussagen, die überall gleich lauten müssen (Block §4.5, README, `CHANGELOG`,
> `admin-ui-reference`, Beispiel-Config):
> 1. Der Grant ist eine **vollständige Shell-Ausweitung** (`Bash`), keine `git`-Beschränkung.
> 2. Der Guard blockt **Sentinel-tragende** Nicht-`git`-Kommandos einer Grant-Rolle (rc 2,
>    Punkte 1–2 oben) — das ist Defense-in-Depth für den wohlgeformten Pfad.
> 3. Kommandos **ohne** Sentinel (Identität = opake `agent_id`) sind keiner Rolle zuordenbar; die
>    Grenze ist damit **keine** Security-Boundary gegen Prompt-Injection. Diese Attributionslücke
>    wird als **#1210** verfolgt (vormals Finding F-5) und in §7.1/§8.2 geführt.
> Die Ack-Pflicht bleibt unverändert Pflicht (D23); ohne `acknowledge_full_shell: true` entsteht
> kein Grant.

**Verworfene Variante:** ein grant-spezifischer Hook-Zweig als *alleinige* Lösung (Review-Variante
a). Er wurde geprüft und als Primärfix verworfen, weil er an der Attributionslücke aus Punkt 3
scheitert (jedes injizierte Kommando ohne Sentinel liefe weiter). Er ist als Härtung aus Punkt 2
enthalten. Die Restlücke ist als **#1210** (vormals Finding F-5, §8.2) erfasst.

### 3.4 Default-Verhalten unverändert

Ohne `authority_overrides`:

- kein Rollen-Template wird verändert,
- kein generierter Agent erhält `Bash` zusätzlich,
- `eligible_roles` ist identisch zu heute,
- `render_auto_commit_block()` liefert dieselben Bytes (Golden-Test).

Das einzige Default-Diff ist das Allowlist-Artefakt: `ALLOWLIST_VERSION` steigt 1 → 2 und die Datei
trägt den zusätzlichen Schlüssel `authority_overrides: {}` (§4.4). Das ist bewusst, additiv und wird
in `CHANGELOG.md` als „Changed“ ausgewiesen (NIT aus dem Review).

### 3.5 Warnung bei schrumpfendem `eligible_roles`

Die Allowlist-Stage liest vor dem Schreiben die vorhandene Datei und vergleicht:

```
previous = json.load(.meta-config/auto-commit-allowlist.json)["eligible_roles"]   (falls Datei existiert)
dropped  = sorted(previous - resolved["eligible_roles"])
```

Für jede weggefallene Rolle wird **genau ein** Grund bestimmt. Die Bedingungen sind disjunkt
definiert und werden in dieser Reihenfolge geprüft (RVW-1181-04):

| # | Grund-Literal | Bedingung (nur geprüft, wenn alle vorherigen nicht greifen) |
|---|---|---|
| 1 | `grant withdrawn` | Rolle stand in der vorherigen Datei unter `authority_overrides` **und** steht im aktuellen Lauf **nicht mehr in `roles:`** (Entzug über die Allowlist, D17) |
| 2 | `role removed` | `roles:`-Key fehlt **oder** die Rolle steht nicht in `roles:` |
| 3 | `gate-dropped` | Rolle steht in `roles:`, aber `active_set.has(role)` ist False |
| 4 | `no Bash` | Rolle steht in `roles:`, ist aktiv, ihre abgeleitete Authority ist nicht `direct` und es gibt keinen aktuellen Grant |

`no Bash` gilt damit ausdrücklich **nur** für Rollen, die in `roles:` stehen; eine aus `roles:`
entfernte Edit-only-Rolle heißt `role removed`, nicht `no Bash`. Die frühere, überlappende
Präzedenz (`grant withdrawn → gate-dropped → no Bash → role removed`) ist ersetzt.

> **DECIDED 2026-11-09 (D17 — OQ-1): Zuordnung der beiden Entzugswege.**
> Der Grant kennt keinen Revoke-Wert; entzogen wird über `roles:` **oder** über das Entfernen des
> Override-Keys. Die beiden Wege sind im Schrumpf-Log bewusst **unterschiedlich** benannt:
> - Rolle **aus `roles:` entfernt** und vorher gegrantet ⇒ `grant withdrawn` **(einziger Ort
>   dieses Literals)**.
> - Nur **Override-Key entfernt**, Rolle bleibt in `roles:` ⇒ `no Bash` (die Rolle ist weiterhin
>   schreibfähig, aber nicht mehr `direct`).
> Ein dritter Grund („grant key removed") wird **nicht** eingeführt: er wäre nicht von `no Bash`
> unterscheidbar, ohne einen weiteren Zustand im Artefakt zu speichern. Die Prüfreihenfolge
> `grant withdrawn → role removed → gate-dropped → no Bash` bleibt disjunkt.

Ausgabe (eine Zeile, sortiert, max. 20 Rollen + `… (+N more)`):

```
[WARN] auto-commit-allowlist: eligible_roles shrank 24 -> 11 (-13): copyeditor (no Bash), documenter (no Bash), planner (no Bash), product-manager (role removed) …
```

Zusätzlich, falls der Modus auf `off` wechselt:

```
[WARN] auto-commit-allowlist: mode changed auto -> off; all 24 eligible role(s) dropped
```

Keine vorherige Datei → `[INFO] auto-commit-allowlist: no previous allowlist — shrink check skipped`.
Datei unlesbar → `[WARN] auto-commit-allowlist: previous allowlist unreadable at <path> — shrink check skipped`.
Die Prüfung läuft **auch im Dry-Run** (vor dem frühen `return` in
`scripts/lib/sync_pipeline.py:1922-1924`), weil sie read-only ist.

### 3.6 Sichtbarkeit des Grants im Sync-Output

Je Grant und aktivem Provider eine Zeile:

```
[INFO] auto-commit-grant: documenter=direct (source: auto_commit.authority_overrides; hook-enforced: yes)
[WARN] auto-commit-grant: planner=direct not enforced on provider 'Opencode' (has_hooks=false); rendered as notify (issue #1181)
```

Bei deaktiviertem Guard entfällt die `yes`-Variante vollständig:

```
[WARN] auto-commit-grant: documenter=direct not enforced (guard hook disabled: hooks.orchestrator-guard.enabled is not true); rendered as notify (issue #1181)
```

Ein Grant auf eine inaktive Rolle (nicht in `roles:` oder vom ActiveSet gedroppt) erzeugt eine
INFO-Zeile aus `authority_override_notices` (§4.3) — **kein** Fehler (D22):

```
[INFO] auto-commit-grant: planner=direct ignored — role is not active (not listed in `roles:` or dropped by the active set)
```

Damit ist „welche Rolle hat Authority bekommen, über welchen Key, und wird sie durchgesetzt“
(Issue-Erwartung 2) ohne Config-Diff beantwortbar.

## 4. Öffentliche Contracts

### 4.1 Schema (Skizze)

`config/project-config.schema.json`, im bestehenden `auto_commit.properties`
(`:1498-1545`); `auto_commit.additionalProperties` bleibt `false` (`:1546`), der Key **muss** daher
explizit in `properties` stehen:

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
      "authority": {
        "type": "string",
        "enum": ["direct"],
        "description": "Escalation target. v1: only 'direct' (delegate/notify are derived automatically; withdrawal runs through the roles: allowlist)."
      },
      "acknowledge_full_shell": {
        "type": "boolean",
        "const": true,
        "description": "Mandatory. Confirms that the grant renders a full Bash permission (a sentinel-carrying command is limited to git add / non-amending git commit; commands without the sentinel are not attributable to the role)."
      }
    }
  },
  "default": {}
}
```

> **DECIDED 2026-11-09 (D23 — OQ-P3): ausschließlich Objektform mit Pflicht-Ack.** `required`
> enthält beide Felder, `additionalProperties: false` verbietet jede Kurzform und jeden
> Zusatzschlüssel. Ein Skalar (`"documenter": "direct"`) ist ein Schema-Fehler und erzeugt keinen
> Grant; ein fehlendes/falsches Ack ebenso (§4.3 Meldungstabelle). **D17:** `enum` bleibt exakt
> `["direct"]` — jeder andere Wert ist ein Fehler, kein Revoke.

Verbindlich (K8): derselbe Key muss in `scripts/lib/auto_commit.py:164` (`_KEYS`) ergänzt werden —
sonst meldet `auto_commit_violations()` „unknown key(s)“ und der bestehende Fail-Safe deaktiviert
die gesamte Commit-Authority (`scripts/lib/auto_commit.py:222-224`, `:269-278`). Schema **und**
`_KEYS` ändern sich deshalb im **selben** PR, und ein Test pinnt die Mengengleichheit
`schema.properties.auto_commit.properties == _KEYS` (bestehendes Muster:
`tests/test_auto_commit_violations.py`, `assert set(_KEYS) == set(ac["properties"])`). Nur das
Schema zu erweitern ist ein Fail-Safe, der #1187 (Scope) weiterlaufen lässt, #1181 aber vollständig
deaktiviert — der Test macht diesen Zustand unmöglich.

### 4.2 Präzedenz (verbindlich, stärkste zuerst)

Die **Wertefolge** bestimmt, welche Authority eine Rolle *hat*. Sie hat sechs Stufen:

| # | Ebene | Wirkung | Beleg |
|---|---|---|---|
| 1 | Ungültiger `auto_commit`-Block (strukturell oder semantisch, inkl. ungültigem Grant oder fehlendem Ack) | Fail-Safe `mode: off`, `eligible_roles: []`, kein Grant, laute Warnung | `scripts/lib/auto_commit.py:269-278`; `scripts/lib/sync_pipeline.py:1909-1915`; `scripts/lib/config.py:1806` (prüft **beide** Verstoßklassen, RVW2-1181-03) |
| 2 | `mode: off` | kein `AUTO_COMMIT_BLOCK`, kein Sentinel (Hook verlangt `auto`/`custom`) | `scripts/lib/auto_commit.py:350-352`; Hook `:459-464` |
| 3 | `roles:`-Allowlist (obere Schranke) | Ohne `roles:`-Key ist `eligible_roles` leer — ein Grant kann keine Rolle hinzufügen, die nicht gelistet ist | `scripts/lib/sync_pipeline.py:1908`; `scripts/lib/active_set.py:59-64` |
| 4 | ActiveSet-Schnitt | gate-dropped/unbekannte Rollen verlieren den Grant still (kein Fehler, aber INFO nach §3.6) | `scripts/lib/sync_pipeline.py:1917-1919`; `scripts/lib/active_set.py:66-67`, `:137` |
| 5 | `auto_commit.authority_overrides.<role>` mit `authority: direct` + `acknowledge_full_shell: true` | eskaliert `delegate`/`notify` → `direct` (Allowlist **und** Render) | diese Spec §3.1/§3.2 |
| 6 | Abgeleitete Authority aus `tools:` | Basisklassifikation | `scripts/lib/auto_commit.py:127-143` |

**Wirkbedingung nach dem Grant (Post-Grant-Demotion, K5).** Das Provider-/Guard-Gate ist **keine**
Präzedenzstufe — es kann keinen Wert *setzen*, nur den bereits vergebenen `direct`-Grant
herabstufen. Es wirkt deshalb **nach** Stufe 5/6:

| Bedingung | Wirkung auf einen bestehenden Grant | Beleg |
|---|---|---|
| Provider ohne verifizierten, gespiegelten Hook | kein `Bash`-Render; Grant bleibt wirkungslos (abgeleitete Klasse), WARN | `scripts/lib/providers.py:700-709` |
| Guard-Hook nicht effektiv aktiv | kein `Bash`-Render (fail closed), WARN + `--validate`-ERROR | `scripts/lib/hooks.py:621-626` |

Beide Bedingungen sind **kumulativ** mit §3.3 (dort Bedingungen 4 und 5) und werden dort geprüft;
die Tabellenreihenfolge oben legt nicht mehr nahe, dass das Gate die schwächste *Wertquelle* sei.

**Orthogonal, keine Präzedenzstufe (unverändert):** `permission-mode-overrides` setzt nur Claude's
`permissionMode`; es vergibt keine Tools und erscheint nicht in der Allowlist. Ein Grant ändert
`permissionMode` nicht, ein `permissionMode` ändert die Authority nicht
(`scripts/lib/roles.py:565-577`; Schema `:518-530`).

Explizit: `permission-mode-overrides: {documenter: bypassPermissions}` macht `documenter` **nicht**
commit-fähig (die Tool-Liste bleibt ohne `Bash`), und
`authority_overrides: {documenter: …}` setzt **kein** `permissionMode`. Die beiden Keys
überschneiden sich nicht.

### 4.3 Funktions-Contracts

**Neu: `scripts/lib/hook_state.py`** (winzige, importfreie Basis für die Hook-Aktivierung; wird von
`hooks.py` und `auto_commit.py` gemeinsam genutzt, damit es genau **ein** Prädikat gibt):

```python
ORCHESTRATOR_GUARD_HOOK = "orchestrator-guard"
ORCHESTRATOR_GUARD_ENABLED_BY_DEFAULT = True

def resolve_hook_enabled(
    hooks_config: Mapping,          # config.get("hooks") or {}
    hook_stem: str,
    enabled_by_default: bool = False,
) -> tuple[bool, bool]:
    """(enabled, invalid_value).

    Exakt die Semantik von hooks._strict_enabled (#1155): nur ein echtes bool
    True aktiviert; ein String "true"/"false" ist invalid (enabled False) und
    wird vom Aufrufer gewarnt.
    """

def guard_hook_enabled(config: dict) -> tuple[bool, bool]:
    """resolve_hook_enabled für ORCHESTRATOR_GUARD_HOOK, Default True."""
```

`scripts/lib/hooks.py::sync_hooks` ruft `resolve_hook_enabled(project_hooks_cfg, hook_stem,
enabled_by_default)` statt der Inline-Auswertung (`:621-626`) und behält die Warnung
`f"hooks.{hook_stem}.enabled: expected true/false (bool), got {raw!r} ({type(raw).__name__}) —
treated as disabled"` im `invalid_value`-Fall. Verhalten und Text bleiben identisch.

`scripts/lib/auto_commit.py`:

```python
def effective_commit_authority(
    role: str,
    agent_meta_root: Path,
    platform: str | None = None,
    authority_overrides: Mapping[str, str] | None = None,
) -> str: ...

def normalize_authority_overrides(raw: object) -> dict[str, str]:
    """{role: "direct"} aus der Config-Form; nur Einträge mit
    authority == "direct" AND acknowledge_full_shell is True. Wirft nie;
    ungültige Einträge werden von authority_override_violations gemeldet."""

def is_role_eligible(
    role: str,
    agent_meta_root: Path,
    platform: str | None = None,
    authority_overrides: Mapping[str, str] | None = None,   # NEU, Default None
) -> bool:
    """True gdw. effective_commit_authority(...) == AUTHORITY_DIRECT."""

def authority_override_violations(
    config: dict,
    agent_meta_root: Path,
    provider_config: Mapping | None = None,   # ai-providers.yaml-Registry; None => selbst laden
) -> list[str]:
    """Semantische Grant-Prüfung; jede Meldung beginnt mit
    'auto_commit.authority_overrides' (Rolle: '…authority_overrides.<role>')."""

def authority_override_notices(
    config: dict,
    active_roles: Iterable[str],
) -> list[str]:
    """INFO-Meldungen für Grants auf inaktive Rollen (kein Fehler).
    active_roles muss die **effektive** aktive Menge sein (raw ∩ ActiveSet.has,
    RVW2-1181-05), sonst fehlt die Notice für gate-dropped Rollen."""

def resolve_commit_grant(
    role: str,
    resolved: dict,
    provider_capabilities: dict | None,
    agent_meta_root: Path,
    *,
    guard_enabled: bool,
) -> tuple[str, bool]:
    """(authority_fuer_diesen_Provider, render_bash).
    render_bash ist nur True bei mode in {auto,custom} AND Grant AND
    provider_hooks_supported(pc) AND guard_enabled AND 'Bash' nicht schon
    im Template. Sonst (derived, False). mode off/suggest => immer
    (derived, False) (D20). Die Auflösung ist per Provider (D21)."""
```

Meldungstexte (stabil, damit Tests und Consumer-CI greppen können):

| Fall | Meldung |
|---|---|
| `authority_overrides` ist kein Mapping | `auto_commit.authority_overrides: expected an object of role -> grant object` |
| Eintrag ist kein Objekt / unbekannter Sub-Key / `authority` ≠ `direct` | `auto_commit.authority_overrides.<role>: expected {authority: direct, acknowledge_full_shell: true}` |
| Ack fehlt oder ist nicht `true` | `auto_commit.authority_overrides.<role>: missing acknowledge_full_shell: true (the grant is a full Bash grant, not a git-only grant)` |
| Rollenname verletzt `^[a-z0-9][a-z0-9-]*$` | `auto_commit.authority_overrides.<role>: role name must match ^[a-z0-9][a-z0-9-]*$` |
| abgeleitete Authority `none` (read-only/unbekannt) | `auto_commit.authority_overrides.<role>: role has no Edit/Write (derived authority is 'none')` |
| Guard nicht effektiv aktiv | `auto_commit.authority_overrides.<role>: grant not enforced (guard hook disabled: hooks.orchestrator-guard.enabled is not true)` |
| kein aktiver Provider mit gespiegeltem Hook | `auto_commit.authority_overrides.<role>: grant not enforced (provider 'Opencode', reason has_hooks=false)` — bei mehreren: `(providers 'Continue', 'Opencode', reason has_hooks=false)` |
| Grant auf inaktive Rolle (INFO, keine Violation) | ``auto_commit.authority_overrides.<role>: grant ignored — role is not active (not listed in `roles:` or dropped by the active set)`` |

Die Enforcement-Prüfung ist bewusst **ERROR nur dann**, wenn der Grant **nirgends** durchsetzbar ist
(Guard aus oder kein aktiver Provider mit Hook). In einem gemischten Set (z. B. Claude + Opencode)
ist die Nicht-Durchsetzung auf dem hook-losen Provider der Normalfall und bleibt die WARN aus §4.6 —
sonst wäre jedes Zwei-Provider-Projekt dauerhaft rot. Die Provider-Registry wird nur geladen, wenn
mindestens ein normalisierter Grant existiert (kein Grant ⇒ keine Violations, kein I/O).

> **DECIDED 2026-11-09 (D21 — OQ-6).** Die Enforcement-Prüfung bewertet die **Zielmenge als
> Ganzes**: sie meldet genau dann, wenn `guard_hook_enabled(config)[0]` False ist **oder** kein
> einziger aktiver Ziel-Provider `provider_hooks_supported(...)` erfüllt. Kann mindestens ein
> Ziel-Provider den Grant durchsetzen, ist die Liste leer; die übrigen Provider erzeugen nur die
> WARN-Zeile aus §4.6. Provider-Namen in der Meldung sind sortiert.

> **DECIDED 2026-11-09 (D22 — OQ-P2).** „Rolle nicht in `roles:`" (oder vom ActiveSet gedroppt)
> ist **kein** Fehler, sondern ausschließlich eine INFO-Zeile aus `authority_override_notices`.
> ERROR bleibt reserviert für (a) read-only/unbekannte Templates (`derived == "none"`) und
> (b) Grants, die nirgends durchsetzbar sind (D21). Der Tippfehler-Fall bleibt damit über (a)
> laut, ohne dass ein legitim abgeschalteter Grant die Validierung rot macht.

> **DECIDED 2026-11-09 (D23 — OQ-P3).** Die Meldungen der Tabelle oben sind die **einzigen**
> Formfehler-Meldungen: Skalar-Kurzform, fehlendes Ack, `acknowledge_full_shell: false` und
> `authority ≠ direct` landen alle in derselben Objektform-Meldung bzw. der Ack-Meldung und
> erzeugen **niemals** einen Grant (auch nicht teilweise).

`role_commit_authority()` bleibt **unverändert** (reine Ableitung, bestens getestet in
`docs/specs/767-auto-commit-permission-authority.md:65-80`); der Grant liegt ausschließlich in der
neuen effektiven Funktion. `AUTHORITY_*`-Literale bleiben die Rückgabewerte.

`resolve_auto_commit_config(config, active_roles, agent_meta_root, platform=None)`:

- ruft künftig `auto_commit_violations` **und** `authority_override_violations`; bei Treffern
  unverändertes Fail-Safe-Dict (`scripts/lib/auto_commit.py:269-278`),
- setzt `eligible_roles` über `is_role_eligible(..., authority_overrides=…)` mit der
  **normalisierten** Map,
- ergänzt das Ergebnis um `"authority_overrides": {role: "direct", …}` (nur Rollen aus
  `active_roles`), damit das Artefakt den Grant auditierbar macht.

**`scripts/lib/config.py::_build_core_variables` (RVW2-1181-03):** Der zweite Render-Pfad
(`:1806`) prüft vor dem Block-Render **ebenfalls** beide Verstoßklassen:
`if auto_commit_violations(config) or authority_override_violations(config, agent_meta_root):`.
Ein Treffer setzt dasselbe Fail-Safe-Dict (`mode: off`, `authority_overrides: {}`) **inklusive**
`INVALID_CONFIG_MARKER`; ohne diese Ergänzung würde ein Grant ohne Ack im
`AUTO_COMMIT_BLOCK` weiter als gültig gerendert. `authority_override_violations` lädt die
Provider-Registry nur, wenn überhaupt ein normalisierter Grant existiert.

### 4.4 Allowlist-Artefakt

`.meta-config/auto-commit-allowlist.json` (geschrieben in
`scripts/lib/sync_pipeline.py:1921-1924`):

```json
{
  "version": 2,
  "mode": "auto",
  "eligible_roles": ["developer", "documenter", "tester"],
  "authority_overrides": { "documenter": "direct" },
  "triggers": ["task-boundary"],
  "file_count_threshold": 5,
  "custom_script": null,
  "secret_scan": true
}
```

- `ALLOWLIST_VERSION` 1 → **2**, weil die Form ein Feld gewinnt. Leser dürfen `version: 1` weiter
  akzeptieren; der Guard-Hook liest `mode`, `eligible_roles` **und** (neu, §3.3.1)
  `authority_overrides` und toleriert ein fehlendes Feld als „kein Grant“
  (`hooks/1-generic/orchestrator-guard-impl.sh:448-478`). Die Map enthält ausschließlich
  `direct`-Einträge (D17); ein entzogener Grant ist ein **fehlender Key**, nie `null`, `false`
  oder ein anderer Authority-Wert.
- **Bewusster Default-Diff (NIT):** die Versionserhöhung schreibt **jedes** Consumer-Artefakt neu,
  auch ohne Grant (`authority_overrides: {}`). Das ist kein Nebeneffekt, sondern die
  Schema-Versionierung des Artefakts; es wird in `CHANGELOG.md` unter „Changed“ genannt und in §9
  der Migration dokumentiert. Alternative wäre ein Feld ohne Versionssprung — verworfen, weil das
  Artefakt dann zwei Formen mit gleicher Versionsnummer hätte.
- Nur **eine** Erhöhung: das neue Feld ist additiv, weitere Leser-Semantik ändert sich nicht.

### 4.5 Render-Vertrag im Agenten

- `AUTO_COMMIT_BLOCK` / `AUTO_COMMIT_ENABLED` bleiben die **einzigen** Platzhalter
  (`scripts/lib/consistency/placeholders.py:79, 104`) — es kommt kein neuer Platzhalter hinzu.
- Der Direct-Block enthält bereits die Sentinel-Zeile (`scripts/lib/auto_commit.py:39-43`,
  eingefügt `:406`, `:435`) und die BOM-/Push-Grenze (`:45-54`).
- Neu, nur für gegrantete Rollen (`role in resolved.get("authority_overrides", {})` **und**
  `authority == direct`), eine zusätzliche Zeile im Block:

  ```
  Granted by project config `auto_commit.authority_overrides.<role>` (issue #1181). This is a
  full `Bash` grant, not a `git`-only grant: the guard hook blocks git mutations outside
  `git add` and a non-amending `git commit`, and rejects your sentinel on any non-git command.
  ```

  Die Formulierung ist Teil des Contracts (AC-2): sie nennt die Ausweitung, nicht nur die Grenze.

> **DECIDED 2026-11-09 (D16 — OQ-3): Persona-Konflikt akzeptiert, Persona unverändert.**
> `documenter` bleibt die Referenzrolle (AC-1), und `agents/1-generic/documenter.md` wird
> **nicht** angefasst — weder Persona-Text noch `tools:`. Der Widerspruch („You implement
> NOTHING" + `Bash`) wird nicht durch eine Rollenänderung aufgelöst, sondern durch die Grant-Zeile
> im Block, die den Grant ausdrücklich als **Commit-Recht** ausweist („Granted by project config
> …"), plus den Doku-Absatz (README, `CHANGELOG`, `admin-ui-reference`). Für alle
> **Nicht-Grant-Rollen** bleibt der Render byte-identisch (§3.4); der Byte-Golden-Test
> (`role=None`) ist davon nicht berührt.

> **DECIDED 2026-11-09 (D20 — OQ-5).** Unter `mode: suggest` wird der Block **ohne** Grant-Zeile
> gerendert (propose-only); die Grant-Zeile existiert nur im `direct`-Zweig von `auto`/`custom`.

- Signaturerweiterung (rückwärtskompatibel):
  `render_auto_commit_block(resolved: dict, authority: str = AUTHORITY_DIRECT, *, role: str | None = None) -> str`.
  `role=None` rendert byte-identisch zu heute.
- Tool-Injektion: `append_frontmatter_tools(content, ["Bash"])`
  (`scripts/lib/frontmatter.py:184-209`) **vor** `transform_agent_content_for_provider`
  (`scripts/lib/agent_sync.py:1010-1025`), weil die Opencode-Permission-Map die Tools aus dem
  Content liest (`scripts/lib/provider_transform.py:1069-1092`). Die bestehende
  MCP-Tool-Injektion läuft bewusst **nach** dem Transform (`agent_sync.py:1027-1040`) und ist
  damit kein geeigneter Ort.

### 4.6 Log-Verträge

| Kanal | Format | Bedingung |
|---|---|---|
| `sync.log` WARN | `auto-commit-allowlist: eligible_roles shrank <old> -> <new> (-<n>): <role> (<reason>), …` | vorherige Datei existiert und `dropped != ∅` |
| `sync.log` WARN | `auto-commit-allowlist: mode changed <old> -> off; all <n> eligible role(s) dropped` | Moduswechsel auf `off` |
| `sync.log` INFO | `auto-commit-allowlist: no previous allowlist — shrink check skipped` | Datei fehlt (Erst-Sync/Upgrade) |
| `sync.log` WARN | `auto-commit-allowlist: previous allowlist unreadable at <path> — shrink check skipped` | JSON/IO-Fehler |
| `sync.log` INFO | `auto-commit-grant: <role>=direct (source: auto_commit.authority_overrides; <enforcement>)` | je Grant und Provider |
| `sync.log` WARN | `auto-commit-grant: <role>=direct not enforced on provider '<P>' (has_hooks=false); rendered as <derived> (issue #1181)` | Grant + hook-loser Provider |
| `sync.log` WARN | `auto-commit-grant: <role>=direct not enforced (guard hook disabled: hooks.orchestrator-guard.enabled is not true); rendered as <derived> (issue #1181)` | Grant + deaktivierter Guard (einmal pro Rolle) |
| `sync.log` INFO | ``auto-commit-grant: <role>=direct ignored — role is not active (not listed in `roles:` or dropped by the active set)`` | Grant auf inaktive Rolle |
| `--validate` | `config-audit [ERROR] auto_commit: auto_commit.authority_overrides.<…>` | semantischer Grant-Verstoß inkl. Nicht-Durchsetzbarkeit (§4.3) |
| Hook stderr + rc 2 | ``ORCHESTRATOR_GUARD: a granted commit role may only use its sentinel for `git add`/`git commit` (issue #1181).`` | Sentinel-tragendes Kommando eines Grant-Rollen-Eintrags, das kein reiner `git add`/`commit`-Scope ist |

Stabile Präfixe (`auto-commit-allowlist:`, `auto-commit-grant:`) sind Teil des Contracts, damit
Consumer-CI sie greppen kann. Zeilenlänge: Rollenliste auf 20 Einträge begrenzen, Rest als
`… (+N more)`.

> **DECIDED 2026-11-09 (D19 — OQ-4): Schrumpf-Warnung bleibt WARN.** Kein `--check`-/`--validate`-
> Gate, keine Exit-Code-Änderung; die Zeile wird bei einem Schrumpf **immer** emittiert, auch im
> Dry-Run, und das Format oben ist byte-stabil (Test pinnt es). Eine Abstimmung mit #1142
> (Exit-Code-Politik) ist ausschließlich eine **spätere** Option und kein Bestandteil dieser
> Spec/Implementierung.

> **DECIDED 2026-11-09 (D21 — OQ-6):** Die Provider-WARN ist **je Provider** eine Zeile; bei
> mehreren hook-losen Providern entsteht je Provider eine eigene Zeile. Die
> `guard hook disabled`-WARN erscheint dagegen **einmal je Rolle** (nicht je Provider), weil der
> Guard global gilt. Positive `hook-enforced: yes`-Zeilen erscheinen nur für Provider, auf denen
> tatsächlich gerendert wird.

## 5. Nicht-Ziele

1. **Keine Rücknahme** bestehender Authority über `authority_overrides` (nur Eskalation `→ direct`,
   Schema-Enum `["direct"]`); Entzug läuft ausschließlich über die `roles:`-Allowlist oder das
   Entfernen des Override-Keys (D17).
2. **Kein** Grant für read-only Rollen (`none`) — das bleibt ein Config-Fehler (§4.3).
3. **Kein** Default-Grant und keine automatische Eskalation aller Edit-only-Rollen.
4. **Keine** Änderung der Hook-Semantik für Rollen **ohne** Grant: der Sentinel-/Mutations-Pfad für
   `git`, `orchestrator` und nativ `direct`-fähige Rollen bleibt byte-gleich. Der Hook ändert sich
   **ausschließlich** um den Grant-Zweig aus §3.3.1 (Sentinel eines Grant-Eintrags nur für
   `git add`/`commit`).
5. **Keine** Änderung an `mode`-Semantik, Trigger-Liste oder `secret_scan`.
6. **Keine** provider-native, kommando-genaue Bash-Permission (z. B. nur `git *`): dafür fehlt im
   Repo ein belegtes Provider-Feature (§7.2, OQ-2/D18). Die einzige kommando-genaue Grenze ist die
   Hook-Härtung aus §3.3.1 und sie gilt nur für Sentinel-tragende Kommandos. Eine Doku-Aussage
   „nur `git`" ist damit ausdrücklich **unzulässig**.
7. **Keine** Ausweitung auf `push`/`tag`/Branch-Management/Merge — unverändert `git`-Rolle
   (Issue #1172 bleibt separat).
8. **Keine** Migration bestehender Consumer-Allowlists; der nächste Sync schreibt sie neu
   (§3.4 Default-Diff).
9. **Kein** Grant ohne effektiv aktiven Guard und ohne verifizierten Provider-Hook: dort wird
   nichts gerendert, sondern gewarnt und `--validate` schlägt fehl (§3.3, §4.3).
10. **Keine** Rollen-Attribution im Hook (agent_id → Rolle). Sie ist im Payload nicht möglich
    (#1210, vormals F-5, §8.2) und wird hier nicht erfunden (D18).

## 6. Akzeptanzkriterien (wörtlich aus #1181)

- [ ] A project config key exists that makes an Edit-only role (`documenter` as the reference case) eligible for `auto_commit` without touching files under `agents/` in the agent-meta repo.
- [ ] The rendered agent honours the grant: the guard-hook sentinel accepts a `git commit` from that role (or a documented, intentional equivalent such as a constrained commit-only Bash permission).
- [ ] Roles without the opt-in keep `bash: deny` — the default rendering is unchanged (no silent widening).
- [ ] A shrink of `eligible_roles` versus the previous allowlist emits a `sync.log` warning listing the dropped roles.
- [ ] Documented in the auto-commit / configuration docs, including precedence vs. `permission-mode-overrides` and `active-set` filtering.

Die AC bleiben **wörtlich** wie im Issue. AC-2 wird in dieser Spec so interpretiert, dass der
Sentinel weiterhin der Durchsetzungspunkt ist und das „constrained commit-only“-Äquivalent die
Hook-Härtung aus §3.3.1 plus die Pflicht-Bestätigung aus §3.1 ist — nicht eine Provider-Permission.
OQ-2 ist mit **D18** entschieden: volle Shell, Hook-Härtung, ehrliche Doku, Attributionslücke
#1210. Die aus dem Review abgeleiteten Zusatz-Abnahmen stehen in §10 (N-1…N-9).

## 7. Risiken & offene Fragen

### 7.1 Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| **Grant = Shell-Rechteausweitung** | Eine bisher Edit-only-Rolle erhält vollen `Bash` (nicht nur `git`). Prompt-Injection in Rollen-Output wird zu Code-Execution: `curl`-Exfiltration, `rm`, `git push`-Versuche | Pflicht-Ack (`acknowledge_full_shell: true`, §3.1); Sentinel-Härtung (§3.3.1 Punkt 2); Provider- **und** Guard-Gate (§3.3); Sync-Log + Artefakt auditierbar; Doku benennt die Ausweitung explizit; Restlücke **#1210** |
| **Attributionslücke im Hook** | Ohne Sentinel kann der Hook kein Kommando einer Rolle zuordnen — Kommando-Grenzen sind umgehbar | Keine kommando-genaue Zusage in Doku/Block (§4.5, D18); Ack-Pflicht; **#1210** als eigenes Ticket; #1151 einordnen |
| Hook-Lücken (#1151) | F6-05 (Sentinel mit leerer `agent_id`), F6-04 (fehlende Mutations-Kommandos) schwächen die „nur add/commit“-Zusage | Grant nur auf Providern mit verifiziertem Hook **und** aktivem Guard; Risiko in der Doku nennen; #1151 vor einem breiten Rollout einordnen (§8.1) |
| Guard im Projekt deaktiviert | `Bash`-Grant ohne jedes Gate = unbeschränkte Shell auf einer Edit-only-Rolle | Bedingung 5 in §3.3 (fail closed, kein Render), WARN §4.6, `--validate`-ERROR §4.3 |
| Hook-lose Provider | Ohne Hook wäre `direct`-Prosa auf einem `bash: deny`-Agenten der #767-Fehler | Grant wird dort nicht gerendert, stattdessen WARN (§3.3, §4.6) |
| Admin-UI löscht den Key | Nutzer speichert im UI und verliert den Grant | `viewProjectAutoCommit` muss unbekannte Keys erhalten oder ein Feld anbieten (§2.4, F-2) |
| Stiller No-op bei Tippfehler im Rollennamen | Grant wirkt nicht, niemand merkt es | semantische Validierung + `--validate`-ERROR + Fail-Safe (§4.3) |
| Grant auf inaktive Rolle | Grant wirkt nicht, bisher ohne Signal | INFO-Notice (§3.6, §4.3) |
| Zwei Key-Listen (Schema `properties` vs. `_KEYS`) | Vergisst man `_KEYS`, deaktiviert der Fail-Safe die ganze Authority | F-1 (§8.2) und ein Test auf Mengengleichheit |
| Persona-Konflikt | `documenter` sagt „You implement NOTHING“, erhält aber `Bash` | **D16: akzeptiert, Persona unverändert.** Grant-Zeile weist den Grant als Commit-Recht aus; jede andere Shell-Nutzung bleibt rollenwidrig; Doku-Absatz (§4.5, §7.1) |
| Grant im falschen Modus erwartet | Nutzer erwartet `Bash` unter `suggest` | **D20:** `suggest` ist propose-only; `resolve_commit_grant` ⇒ `(derived, False)`; Doku nennt es (T11) |
| Artefakt-Churn durch `version: 2` | Jeder Consumer sieht eine geänderte Allowlist, auch ohne Grant | Bewusster Default-Diff, in `CHANGELOG` „Changed“ und §3.4/§4.4 dokumentiert |

### 7.2 Offene Fragen (alle entschieden 2026-11-09)

| ID | Frage | Entscheidung 2026-11-09 (verbindlich) |
|---|---|---|
| OQ-1 | Soll `authority_overrides` in v1 auch `delegate`/`notify`/`none` akzeptieren (Entzug)? | **DECIDED (D17): nein.** Schema-Enum bleibt `["direct"]`. Entzug ausschließlich über `roles:` oder Entfernen des Override-Keys; `grant withdrawn` bleibt an die `roles:`-Entfernung gebunden (§3.5). |
| OQ-2 | Unterstützt ein Ziel-Provider eine kommando-genaue Bash-Permission (z. B. nur `git add`/`git commit`)? Im Repo gibt es dafür keinen Beleg: `provider_transform.py:895-920` mappt Skalare, v2 nutzt `resource: "*"` (`:960-972`). | **DECIDED (D18): nein.** Grant = voller `Bash`; die Doku sagt das ausdrücklich, keine „nur `git`"-Aussage. Kommando-genaue Grenze ausschließlich über die Hook-Härtung (§3.3.1) für Sentinel-tragende Kommandos; Attributionslücke = **#1210**. |
| OQ-3 | Ist der Persona-Konflikt („implementiert nichts“ + `Bash`) akzeptabel? | **DECIDED (D16): ja.** `documenter` bleibt Referenzrolle, `agents/1-generic/documenter.md` wird nicht geändert; der Grant wird im `AUTO_COMMIT_BLOCK` als Commit-Recht ausgewiesen und in der Doku erklärt. |
| OQ-4 | Soll die Schrumpf-Warnung unter `--check`/`--validate` ein ERROR (CI-Gate) sein? | **DECIDED (D19): WARN.** Kein CI-Gate, exaktes Log-Format bleibt gepinnt. Abstimmung mit #1142 nur als spätere Option. |
| OQ-5 | Gilt der Grant auch für `suggest`? | **DECIDED (D20): nein.** `resolve_commit_grant` liefert für `suggest` `(derived, False)`; kein `Bash`-Render, kein Sentinel. |
| OQ-6 | Soll ein Grant auf einem hook-losen Provider in einem **gemischten** Provider-Set ein ERROR sein? | **DECIDED (D21): nein.** Auf Providern mit aktivem Guard wird gerendert, auf den übrigen bleibt die abgeleitete Authority + WARN je Provider. ERROR nur, wenn der Grant auf **keinem** Ziel-Provider wirken kann. |
| OQ-P2 | Ist „Rolle nicht in `roles:`" ein Fehler? | **DECIDED (D22): nein, INFO.** `authority_override_notices` liefert eine INFO-Zeile; ERROR bleibt für read-only/unbekannte Templates und nicht durchsetzbare Grants. |
| OQ-P3 | Skalar (`documenter: direct`) oder Objekt mit Pflicht-Ack? | **DECIDED (D23): nur Objektform** `{authority: direct, acknowledge_full_shell: true}`. Skalar-Kurzform wird nicht akzeptiert; fehlendes/falsches Ack = Violation + kein Grant. |

## 8. Backlog-Bugs & Findings

### 8.1 Bestehende Issues — Einordnung

| Issue | Titel (kurz) | Einordnung zu #1181 | Begründung |
|---|---|---|---|
| #1142 | `invalid auto_commit still exits 0 …, writes the allowlist, missing from --validate summary` | **Parallel, Vorbedingung für die Doku-Aussage** | #1181 erbt den #1091-Fail-Safe und fügt eine zweite Verstoßklasse hinzu. Wenn #1142 „kein Allowlist-Write bei ungültigem Block“ oder harte Exit-Codes einführt, muss §4.2/§4.6 dieser Spec darauf verweisen. Kein Code-Konflikt (andere Funktionen), aber dieselbe Semantik. |
| #1151 | `NotebookEdit/MultiEdit/PowerShell bypass containment and strict-mode guards; allowlist drift` | **Sicherheitsabhängigkeit, kein Blocker** | Der Grant stützt seine Zusage „nur add/commit“ auf den Guard-Hook. F6-05/F6-04/F6-06 schwächen diese Zusage. Umsetzbar parallel, aber Rollout-/Doku-Reihenfolge dokumentieren. |
| #1172 | `merges dispatched via orchestrator to git agent are blocked …` | **Unabhängig, abgegrenzt** | Merge/Push/Tag bleiben `git`-Rolle (§5 Nr. 7). Berührungspunkt nur in `rules/1-generic/use-orchestrator.md`, das #1181 nicht ändert. |
| **#1210** | `bug(hooks): PreToolUse payload carries agent_id but no agent name — command-level scoping for granted roles is not enforceable` | **Dokumentierte Grenze, kein Blocker** | Das Payload trägt keine Rolle; kommando-genaue Zusagen gelten nur für Sentinel-tragende Kommandos (§3.3.1 Punkt 3, D18). Die Spec/Doku benennt die Lücke ausdrücklich statt sie zu verschweigen; #1181 liefert die Härtung für den wohlgeformten Pfad. |

### 8.2 Neue Findings (F-5 = #1210)

**F-1 — Zwei handgepflegte Key-Listen governen `auto_commit`**

- Titelvorschlag: `bug(config): auto_commit key allowlist exists twice (schema properties vs. _KEYS) — a new key silently disables commit authority`
- Labels: `bug`, `config`, `sync`, `P3`
- Body-Skizze: `config/project-config.schema.json:1495-1546` deklariert die erlaubten Keys und
  `additionalProperties: false`; `scripts/lib/auto_commit.py:164` führt dieselbe Menge als `_KEYS`.
  Ein Key, der nur im Schema landet, erzeugt „auto_commit has unknown key(s)“ (`:222-224`) und
  deaktiviert per Fail-Safe (`:269-278`) die gesamte Commit-Authority. Vorschlag: `_KEYS` aus dem
  Schema ableiten (oder Test auf Mengengleichheit), analog zur Forderung in #1186 AC-7 für
  `PROJECT_WRITABLE_SECTIONS`.

**F-2 — Admin-UI verwirft unbekannte `auto_commit`-Keys beim Speichern**

- Titelvorschlag: `bug(admin-ui): saving the auto-commit panel drops keys the form does not know (authority_overrides, future keys)`
- Labels: `bug`, `config`, `admin-ui`, `P3`
- Body-Skizze: `docs/ui/admin-ui.html:7753-7760` baut `out` aus den bekannten Feldern und sendet nur
  dieses (`:7761`). Jeder neue Key (heute `authority_overrides`, künftig weitere) wird beim
  UI-Speichern still gelöscht. Repro: Key in `project.yaml` setzen, Panel öffnen, „Save“ →
  Key verschwindet. Vorschlag: unbekannte Keys aus `ac` übernehmen (`const out = { ...ac, mode };`)
  oder ein explizites Feld rendern; Test auf Round-Trip-Erhalt.

**F-3 — Zeilenbelege in der freigegebenen Spec #767 sind veraltet**

- Titelvorschlag: `docs(spec): 767 references stale file:line anchors (auto_commit/config/sync_pipeline/hook)`
- Labels: `docs`, `P3`
- Body-Skizze: `docs/specs/767-auto-commit-permission-authority.md` verweist u. a. auf
  `auto_commit.py:14`, `:32-39`, `:85-169`, `config.py:1302-1315`,
  `sync_pipeline.py:1479-1494`, `hooks/1-generic/orchestrator-guard-impl.sh:201-232`. Aktuell sind
  es `auto_commit.py:28`, `:127-143`, `:322-459`, `config.py:1792-1848`,
  `sync_pipeline.py:1893-1924`, Hook `:420-502`. Vorschlag: bei der Umsetzung von #1181 die
  Anker mitziehen (ohne die Spec inhaltlich neu zu verhandeln).

**F-4 — Spec zitiert den toten Bash→`code_execution`-Mapper für Gemini**

- Titelvorschlag: `docs(spec): #1181 cites the dead Bash→code_execution mapper for Gemini`
- Labels: `docs`, `P3`
- Body-Skizze: `_map_claude_tools_to_gemini_tools()` (`scripts/lib/provider_transform.py:854-870`)
  hat keinen Aufrufer; `config/provider-capabilities.yaml:290` listet ihn selbst als offene
  Inkonsistenz. Der lebende Render-Pfad ist `agent-transform.tool-name-map`
  (`config/ai-providers.yaml:230-251`, `Bash: run_command`); `bash_tool_name: code_execution`
  (`:203`) gehört zur Enforcement-Seite. **Status: mit Rev. 1.1 dieser Spec geschlossen** (§3.3);
  das Ticket bleibt für den toten Code selbst (Löschung oder Reaktivierung).

**F-5 / #1210 — Hook kann ein Kommando ohne Sentinel keiner Rolle zuordnen**

- **Issue:** #1210 (verknüpft laut **D18**; vormals Finding F-5 ohne Nummer)
- Titelvorschlag: `bug(hooks): PreToolUse payload carries agent_id but no agent name — command-level scoping for granted roles is not enforceable`
- Labels: `bug`, `hooks`, `security`, `P3`
- Body-Skizze: Der Guard liest die Rolle ausschließlich aus dem modell-geschriebenen Sentinel
  (`orchestrator-guard-impl.sh:326-350`); das Payload liefert nur `agent_id` (`:262-269`). Damit ist
  jede kommando-genaue Begrenzung, die an eine Rolle gebunden ist, für Kommandos **ohne** Sentinel
  wirkungslos — genau der Injection-Pfad. Vorschlag: Harness-Fähigkeit prüfen (gibt es ein
  Rollen-/Agenten-Namensfeld im Payload?), sonst die Grenze dokumentieren und den Grant als
  Voll-Shell-Grant führen (was diese Spec tut, §3.3.1).

## 9. Cross-Issue-Konfliktflächen

### 9.0 Kanonische Ausführungsreihenfolge (verbindlich, Querschnitt)

```
#1187 → #1186 → #1188 → #1181 → #1141;  Whitelist-Ableitung zuletzt.
```

Begründung: #1187 baut die Rollen-Schleife in `scripts/lib/agent_sync.py` um, auf der #1181
aufsetzt; #1186/#1188 ändern Schema, Scaffolding und Admin-UI-Panes, die #1181 ebenfalls berührt.
Szenario-IDs: **`94` = #1181** (bestätigt, letzte vergebene ID ist `93`,
`tests/scenarios/registry.md:132`), **`95–98` = #1187**. `docs/issue-labels.md` (entsteht in #1188)
wird in **#1186** klassifiziert — nicht in #1181.

### 9.1 Matrix

| Datei | Issues | Konfliktnatur | Serialisierung |
|---|---|---|---|
| `config/project-config.schema.json` | #1181, #1186, #1187, #1188 | Alle vier ergänzen Top-Level-Sections; #1181 ändert zusätzlich den `additionalProperties: false`-Block `auto_commit` (`:1495-1546`) | **Ja, seriell** — ein PR nach dem anderen, sonst Hunk-Kollisionen im Root-`properties` |
| `scripts/lib/config.py` | #1181, #1186, #1187, #1188 | Gemeinsames Modul; #1181 nutzt `_build_core_variables` (`:1792-1848`), die anderen fügen neue Resolver/Variablen hinzu | **Ja, seriell** (Kontextüberlappung, keine semantische Überschneidung) |
| `scripts/lib/agent_sync.py` | **#1187, #1188, #1181** | **Dieselbe Rollen-Schleife**: #1187 baut `sync_agents_for_provider` / `_finalize_agent_content` um; #1188 ergänzt dort Provider-/Pane-Aufrufe; #1181 hängt dort `_apply_role_auto_commit_overrides` (`:92-123`), den Aufruf im Rollenloop (`:1457-1468`) und den `extra_tools`-Parameter an `_finalize_agent_content` (`:935`, Transform `:1010`) | **Ja, seriell** — #1181 nach #1187/#1188 |
| `scripts/lib/sync_pipeline.py` | **#1186, #1181** (#1187 nur bei echtem Task) | #1181 baut Stage 14 (`:1893-1924`) um (Shrink-Vergleich, Grant-Logs); #1186 ergänzt Scaffolding/Stages und `ARTIFACT_*`; #1187 fasst denselben Stage-Block nur an, wenn es dort einen echten Task hat | **Ja, seriell** (Stage-Reihenfolge + Hash-Capture-Semantik) |
| `scripts/lib/variables.py` | **#1187** (nicht #1181) | `conditional_vars` listet `AUTO_COMMIT_ENABLED` (`:572`); #1187 ergänzt dort weitere Bedingungs-Variablen in derselben Menge. #1181 ändert die Datei nicht | Nein für #1181 |
| `scripts/lib/standalone.py` | **#1187** (nicht #1181) | Platzhalter-Defaults (`AUTO_COMMIT_BLOCK` `:97`, `AUTO_COMMIT_ENABLED` `:152`); #1181 fügt **keinen** Platzhalter hinzu, #1187 ändert Defaults in derselben Tabelle | Nein für #1181 |
| `docs/ui/admin-ui.html` | #1181, #1186, #1187, #1188 | Vier Panes in einer 489-KB-Datei; #1181 ändert `viewProjectAutoCommit` (`:7639-7766`), die anderen fügen Panes/Router-Einträge hinzu | **Ja, seriell** |
| `scripts/admin-server.py` | #1186, #1187, #1188 | `PROJECT_WRITABLE_SECTIONS` (`:230-249`); #1181 braucht **keine** Änderung, `auto_commit` ist bereits gelistet (`:252`) | Nein (nur indirekt, falls #1186 die Whitelist ableitet) |
| `scripts/lib/consistency/placeholders.py` | #1186, #1188 | Neue Platzhalter-Allowlist-Einträge; #1181 fügt **keinen** Platzhalter hinzu | Nein |
| `hooks/1-generic/orchestrator-guard-impl.sh` | #1181, #1151 | #1181 ergänzt den Grant-Zweig (§3.3.1: Klassifizierer-Feld `all_git`, Gate); #1151 härtet denselben Hook | **Ja, seriell** — #1151 zuerst, dann #1181 (sonst doppelte Arbeit an denselben Zeilen) |
| `scripts/lib/hooks.py` + `scripts/lib/hook_state.py` (neu) | #1181 (nur) | `resolve_hook_enabled` wird aus `sync_hooks` herausgezogen; `hook_state.py` ist neu | Nein |
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CODEBASE_OVERVIEW.md` | alle vier | Dieselben Doku-Dateien, jeweils neue Abschnitte; #1181 ergänzt `README.md:477-500` | **Ja, seriell** (kurze, klar abgegrenzte Hunks) |
| `templates/configs/project.yaml.example` | **#1187, #1186, #1188, #1181** | `# auto_commit:`-Kommentarblock (`:91`); #1181 dokumentiert dort `authority_overrides`, die anderen ergänzen Nachbarblöcke | **Ja, seriell** |
| `docs/guides/project.yaml.example`, `howto/configs/project.yaml.example` | **#1187, #1186, #1188, #1181** | Weitere Kopien der Beispiel-Config; #1181 ändert sie **nicht** inhaltlich (kein `auto_commit`-Block dort), muss sie aber beim Merge gegen die Vorgänger prüfen | **Ja beim Mergen** |
| `docs/api/admin-ui-reference.md` | #1181 (nur) | Help-Text `auto_commit` (`:182-185`) | Nein |
| `tests/scenarios/registry.md` + Assert-Dateien | **#1181, #1187, #1186** | Gemeinsame Szenario-Nummerierung (`94` = #1181, `95–98` = #1187) und `tests/scenarios/asserts/*` | **Ja** (Nummernvergabe abstimmen) |
| `config/provider-tools.yaml` | #1181 (keine Änderung) | `opencode_deny_critical` bleibt unverändert; die Ausnahme entsteht über die Tool-Liste | Nein |
| `docs/issue-labels.md` | **#1188 erzeugt, #1186 klassifiziert** | Die Datei entsteht in #1188; die Label-Klassifikation ist #1186 | Nicht #1181 |
| `.meta-config/issue-labels-state.json` | **#1188 erzeugt, #1186 klassifiziert als `unmanaged`** (K1; `project-state` ist gestrichen) | Projekt-State-Artefakt der Label-Taxonomie, Negativ-Deklaration ohne Klasse | Nicht #1181 |

## 10. Traceability: Akzeptanzkriterien → Spec-Abschnitte

| AC | Wortlaut-Kern | Deckende Abschnitte | Nachweis (geplant) |
|---|---|---|---|
| AC-1 | Config-Key macht Edit-only-Rolle eligibel, ohne `agents/` zu ändern | §3.1, §3.2, §4.1, §4.3, §4.4 | Schema-Test + `test_auto_commit_authority_grants.py`: `documenter` in `eligible_roles`; `git diff --name-only aaed14c2..HEAD -- agents/` ist leer (commit-fest, RVW2-1181-02) |
| AC-2 | Gerenderter Agent honoriert den Grant (Sentinel akzeptiert Commit bzw. dokumentiertes Äquivalent) | §3.3, §3.3.1, §4.4, §4.5, §4.6 | Render-Test (Claude: `Bash` in `tools:`, Block mit Grant-Zeile), Hook-Test mit `eligible_roles`-Eintrag; Gemini: `run_command` (nicht `code_execution`); positive `bash: allow`/`shell: allow`-Fälle nur gegen synthetischen Hook-Fixture; Opencode real nur `bash: deny` + WARN (RVW2-1181-01) |
| AC-3 | Rollen ohne Opt-in behalten `bash: deny`, Default unverändert | §3.4, §4.2 (Nr. 2/5/6) | Golden-Test „ohne Key byte-identisch“; `documenter` ohne Grant weiter `bash: deny` |
| AC-4 | Schrumpf von `eligible_roles` erzeugt `sync.log`-Warnung mit Rollenliste | §2.2, §3.5, §4.6 | Pipeline-Test: vorherige Allowlist mit 24 Rollen, Sync mit 11 → exakte WARN-Zeile mit disjunkten Gründen |
| AC-5 | Dokumentation inkl. Präzedenz gegen `permission-mode-overrides` und `active-set` | §1, §3, §4.2, §4.6, §7 | `README.md`-Abschnitt „Auto-commit“ + `docs/api/admin-ui-reference.md`; Doku verweist auf diese Spec |

**Zusätzliche Abnahmekriterien aus Review und Entscheidungen (nicht Teil des Issue-Wortlauts):**

| ID | Kriterium | Abschnitt | Nachweis |
|---|---|---|---|
| N-1 | Ein Projekt mit `hooks.orchestrator-guard.enabled: false` bekommt **kein** `Bash` gerendert und `--validate` endet mit rc 1 | §3.3 (5), §4.3, §4.6 | Sync-Test (Claude + Grant + Guard aus) ⇒ Frontmatter ohne `Bash`; `--validate`-Test ⇒ `grant not enforced (guard hook disabled …)` |
| N-2 | Ein Grant ohne `acknowledge_full_shell: true` ist ein Config-Fehler und rendert nichts | §3.1, §4.1, §4.3 | Schema-Test (`acknowledge_full_shell` fehlt/`false` ⇒ `ValidationError`); `--validate`-rc 1; Fail-Safe-Dict |
| N-3 | Ein Sentinel-tragendes Nicht-`git`-Kommando einer gegranteten Rolle endet mit rc 2 | §3.3.1 (2), §4.6 | Hook-Test: `#agent-meta:agent=documenter\ncurl https://example.invalid` ⇒ rc 2 |
| N-4 | Ein Grant, der nirgends durchsetzbar ist (Guard aus oder nur hook-lose Provider), ist ein `--validate`-ERROR; im gemischten Set nur WARN | §4.3, §4.6 | Zwei `--validate`-Tests (nur Opencode ⇒ rc 1; Claude+Opencode ⇒ rc 0 + WARN) |
| N-5 | Ein Grant unter `mode: suggest` rendert kein `Bash` und keine Grant-Zeile (D20) | §3.3 (D20), §4.5 | `resolve_commit_grant`-Test `(notify, False)` + Render-Test ohne `#1181`-Zeile |
| N-6 | Im gemischten Set wird auf dem hook-fähigen Provider gerendert, auf dem hook-losen nur gewarnt (D21) | §3.3 (D21), §4.6 | Sync-Test Claude+Opencode: `Bash` in `.claude/agents/documenter.md`, `bash: deny` in `.opencode/…` + genau eine WARN je hook-losem Provider |
| N-7 | Rolle nicht in `roles:` ⇒ INFO, kein Fehler (D22) | §3.6, §4.3 | `authority_override_notices`-Test liefert genau eine INFO-Zeile; `--validate` rc 0 |
| N-8 | Entzug: Rolle aus `roles:` entfernt ⇒ `grant withdrawn`; nur Override-Key entfernt ⇒ `no Bash` (D17) | §3.5 | Zwei Pipeline-Tests mit exakt diesen Reason-Literalen |
| N-9 | `agents/1-generic/documenter.md` bleibt unverändert; Byte-Golden für Nicht-Grant-Rollen bleibt grün (D16) | §3.4, §4.5 | `git diff --name-only aaed14c2..HEAD -- agents/` leer; fünf Byte-Golden-Fälle (`role=None`) unverändert grün |

## 11. Betroffene Dateien (Reihenfolge für die Umsetzung)

1. `config/project-config.schema.json` — `auto_commit.properties.authority_overrides` (Objektform).
2. `scripts/lib/hook_state.py` (**neu**) — `resolve_hook_enabled`, `guard_hook_enabled`,
   `ORCHESTRATOR_GUARD_*`.
3. `scripts/lib/hooks.py` — `sync_hooks` nutzt `resolve_hook_enabled` (verhaltensgleich).
4. `scripts/lib/auto_commit.py` — `_KEYS`, `ALLOWLIST_VERSION`, `normalize_authority_overrides`,
   `authority_override_violations`, `authority_override_notices`, `effective_commit_authority`,
   `is_role_eligible`-Erweiterung, `resolve_auto_commit_config`, `render_auto_commit_block(...,
   *, role=None)`, `resolve_commit_grant`.
5. `scripts/lib/config.py` — `_AUTO_COMMIT_RESOLVED` trägt `authority_overrides` und der
   Fail-Safe prüft `auto_commit_violations` **und** `authority_override_violations`
   (`:1792-1848`, RVW2-1181-03).
6. `scripts/lib/agent_sync.py` — `_apply_role_auto_commit_overrides` (Provider-/Guard-Gate,
   Grant-Zeile, Rückgabe `render_bash`) und `_finalize_agent_content(..., extra_tools=…)` **vor**
   dem Transform (`:1010`), Aufrufstelle im Rollenloop (`:1457-1468`).
7. `hooks/1-generic/orchestrator-guard-impl.sh` — Grant-Zweig (§3.3.1): viertes Klassifizierer-Feld,
   Sentinel-Gate, Versionsbump `1.11.0 → 1.12.0`.
8. `scripts/lib/sync_pipeline.py` — Shrink-Vergleich mit disjunkten Gründen, Grant-/Skip-/Notice-Logs,
   `version: 2` (`:1893-1924`).
9. `docs/ui/admin-ui.html` — Key-Erhalt in `viewProjectAutoCommit` (`:7639-7766`).
10. `scripts/lib/cli_commands.py` — semantische Grant-Verstöße und Notices in `--validate`
    (Einfügepunkt nach `_provider_config = _load_pc(agent_meta_root)` `:1462`; die bestehende
    `auto_commit_violations`-Schleife bleibt `:1432-1439`).
11. `README.md` (`:477-500`), `docs/api/admin-ui-reference.md` (`:182-185`),
    `templates/configs/project.yaml.example` (`:91`).
12. Tests: `tests/test_auto_commit_schema.py`, `tests/test_auto_commit_violations.py`,
    `tests/test_auto_commit_lib.py`, `tests/test_auto_commit_block_render.py`,
    `tests/test_auto_commit_allowlist_pipeline.py`, `tests/test_orchestrator_guard_hook.py`;
    neu `tests/test_auto_commit_authority_grants.py`, `tests/test_hook_state.py`,
    `tests/test_admin_ui_auto_commit_section.py`; Szenario-Config + Assert (`94`).
13. `CHANGELOG.md` (Unreleased) und `docs/specs/767-auto-commit-permission-authority.md`
    (Zeilenanker, F-3).

## 12. Review-Auflösung (2026-11-09)

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **RVW-1181-01** (BLOCKER) | Gate prüft jetzt die **effektive** Hook-Aktivierung über `hook_state.resolve_hook_enabled` (dasselbe Prädikat wie `hooks.sync_hooks`, Reviewer-Anker `hooks.py:622-626`); neue Bedingung 5 in §3.3, `guard_enabled`-Parameter in `resolve_commit_grant`, `--validate`-ERROR bei Grant ohne aktiven Guard. Test mit `hooks.orchestrator-guard.enabled: false` als N-1. | §3.3, §3.3.1, §4.2 (Wirkbedingung), §4.3, §4.6, §10 (N-1) |
| **RVW-1181-02** (MAJOR) | Variante **(b)** vollständig durchgezogen: `authority_overrides.<role>` ist ein Objekt mit Pflichtfeld `acknowledge_full_shell: true`; Schema, Normalisierung, Violation, Render-Zeile und Doku benennen die volle Shell-Ausweitung. Zusätzlich als Defense-in-Depth: Sentinel-Härtung für Grant-Rollen (§3.3.1 Punkt 2). Variante (a) als Primärfix mit Begründung verworfen (Attributionslücke, F-5). | §3.1, §3.3.1, §4.1, §4.3, §4.5, §5 (4/6/9/10), §7.1, §8.2 (F-5), §10 (N-2/N-3) |
| **RVW-1181-03** (MAJOR) | Neues `--validate`-Finding `auto_commit.authority_overrides.<role>: grant not enforced (…)` mit zwei Ursachen (Guard aus, kein aktiver Hook-Provider); Abgrenzung ERROR vs. WARN im gemischten Set (OQ-6). Tests für hook-losen Provider und deaktivierten Guard als N-1/N-4. | §4.3 (Meldungstabelle), §4.6, §7.2 (OQ-6), §10 (N-1/N-4) |
| **RVW-1181-04** (MAJOR) | K-5-Präzedenz ersetzt: Gründe sind jetzt **disjunkt** definiert (`no Bash` nur für Rollen in `roles:`), Prüfreihenfolge `grant withdrawn → role removed → gate-dropped → no Bash`. Damit ist `product-manager (role removed)` konsistent; das T9-Fixture im Plan wurde entsprechend korrigiert. | §3.5 (Tabelle + Reihenfolge), §4.6 |
| **RVW-1181-05** (MINOR) | Gemini-Zeile korrigiert: lebender Pfad ist `config/ai-providers.yaml:230-251` (`Bash: run_command`), `code_execution` nur `bash_tool_name` (`:203`); toter Mapper als F-4 ausgewiesen. AC-2-Traceability nennt `run_command`. | §3.3 (Tabelle + Korrekturabsatz), §6, §8.2 (F-4), §10 (AC-2) |
| **RVW-1181-06** (MINOR) | Baseline-Zahlen korrigiert (siehe Plan §8: 75 gesamt = 3/20/4/1/**17**/12/**18**); Gates stützen sich zusätzlich auf `0 failed` + benannte Tests statt auf Sollzahlen. | Plan §5, §8 (angeglichen) |
| **Signatur-WARN** | `resolve_commit_grant` führt `agent_meta_root` (K-1) **und** `guard_enabled` in der Spec; `authority_override_violations` bekommt `provider_config`. | §4.3, §3.2 |
| **T14-WARN** | T14 ist im Plan als reine Verifikation gekennzeichnet (`Files: — (Verifikation)`). | Plan §4, T14 |
| **NIT `ALLOWLIST_VERSION`** | Versionssprung 1 → 2 als bewusster Default-Diff für alle Consumer dokumentiert (auch ohne Grant). | §3.4, §4.4, §7.1 |
| **NIT `active_roles`** | Parameter wird genutzt: neue `authority_override_notices` liefert INFO bei inaktiver Rolle; aus `authority_override_violations` entfernt, damit kein toter Parameter bleibt. | §3.6, §4.3, §4.6 |
| **Querschnitt** | Kanonische Reihenfolge `#1187 → #1186 → #1188 → #1181 → #1141`, Szenario-IDs `94`/`95–98`, erweiterte Konfliktmatrix inkl. `variables.py`, `standalone.py`, `registry.md`, beider/aller `project.yaml.example`-Dateien und `docs/issue-labels.md` → #1186. | §9.0, §9.1 |
| **RVW2-1181-01** (MAJOR) | Render-Vertrag bereinigt: Opencode v1/v2 ist **kein** positiver Render-Fall (`config/ai-providers.yaml:274` `has_hooks: false`; `config/provider-capabilities.yaml:179` `hooks: false`). Die beiden Zeilen sind aus der Render-Tabelle entfernt; Opencode steht nur noch unter „hook-lose Provider". Der einzige reale Opencode-Fall ist `bash: deny`/`shell: deny` + WARN. Positive `bash: allow`/`shell: allow`-Tests nur gegen einen synthetischen hook-fähigen Capability-Fixture. | §3.3 (Tabelle + Absatz), §7.2 (OQ-6), §10 (AC-2) |
| **RVW2-1181-02** (MAJOR) | AC-1-Nachweis commit-fest: statt `git diff --stat agents/` (nach dem Commit vakuum-grün) jetzt `git diff --name-only aaed14c2..HEAD -- agents/`. | §10 (AC-1) |
| **RVW2-1181-03** (MAJOR) | Fail-Safe auch im zweiten Render-Pfad: `_build_core_variables` (`scripts/lib/config.py:1806`) prüft `auto_commit_violations` **und** `authority_override_violations`; ein Treffer setzt `mode: off`, `authority_overrides: {}` und `INVALID_CONFIG_MARKER`. | §4.2 (Nr. 1), §4.3 |
| **RVW2-1181-04** (MINOR) | `effective_commit_authority` bekommt einen Mapping-Guard: ein Nicht-Mapping (`authority_overrides=["x"]`) wird wie „kein Grant" behandelt statt `AttributeError`; der Vertrag „wirft nie" gilt damit auch für Typfehler des Aufrufers. | §3.2 (Nr. 2/5) |
| **RVW2-1181-05** (MINOR) | `authority_override_notices` erhält die **effektive** aktive Menge (raw ∩ `active_set.has`), damit auch gate-dropped Rollen die INFO-Notice auslösen; Test mit gate-dropped Rolle. | §3.6, §4.3 (Signatur-Docstring) |
| **RVW2-X-01** (MAJOR, Querschnitt) | Zielmatrix auf die verbindliche Fassung angeglichen: `agent_sync.py` → #1187/#1188/#1181; `sync_pipeline.py` → #1186/#1181 (#1187 nur bei echtem Task); `variables.py`/`standalone.py` → #1187; `registry.md` → #1181/#1187/#1186; beide `project.yaml.example` → #1187/#1186/#1188/#1181; `docs/issue-labels.md` und `.meta-config/issue-labels-state.json` → #1188 erzeugt, #1186 klassifiziert. | §9.0, §9.1 |

---

### 12.1 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Status bleibt `DRAFT`.

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` wird als **`unmanaged`** klassifiziert (Negativ-Deklaration, #1186); `project-state` gestrichen | **§9.1** (Matrix-Zeile) |
| **K2** | **Nicht betroffen**: kein Label-Separator im `auto_commit`-Vertrag | geprüft: §3.1 |
| **K3** | **Nicht betroffen**: die Stufen-Tabelle ist eine Authority-, keine Preset-Präzedenz | geprüft: §4.2 |
| **K4** | **Nicht betroffen**: keine `taxonomyAxis` | geprüft: §4.1 |
| **K5** (MINOR) | Das Provider-/Guard-Gate ist **keine Präzedenzstufe 7**, sondern eine **Wirkbedingung nach dem Grant** („Post-Grant-Demotion"). Die Tabelle führt nur noch die sechs Wertstufen; das Gate steht als eigener Block darunter, `permission-mode-overrides` bleibt explizit orthogonal. Die Wertefolge 1–6 ist unverändert | **§4.2** (Tabelle + zwei neue Blöcke) |
| **K6** | **Nicht betroffen**: der Schema-Sketch ist inline, ohne `$defs` | geprüft: §4.1 |
| **K7** (NIT) | Innerhalb der snake_case-Sektion `auto_commit` gilt snake_case: `acknowledge-full-shell` → **`acknowledge_full_shell`** (alle Vorkommen, auch Schema `required` und Meldungstexte). Der Stilsatz ist einmal explizit dokumentiert (neue Top-Level-Sektionen kebab-case, Schlüssel erben den Stil ihrer Sektion) | **§3.1** (Namensstil-Absatz), §4.1, §4.3, §4.5, §4.6, §7.1, §10 |
| **K8** | Schema **und** `_KEYS` (`scripts/lib/auto_commit.py:164`) ändern sich im **selben** PR, plus Mengengleichheits-Test `schema.properties.auto_commit.properties == _KEYS`; „nur Schema" ist ausdrücklich ein Fail-Safe, der #1181 deaktiviert | **§4.1** (Verbindlich-Absatz) |

---

## 13. Entscheidungsprotokoll (2026-11-09)

Alle offenen Fragen dieser Spec sind durch den Nutzer entschieden. Die Nummern `D16–D23` sind
fortlaufend aus der Wave-Konvention (D1–D15 gehören zu den Schwester-Specs #1186/#1187/#1188) und
gelten in Spec **und** Plan identisch.

| D-Nr | Frage | Entscheidung | Stelle |
|---|---|---|---|
| **D16** | OQ-3 — Ist der Persona-Konflikt „`documenter` implementiert nichts" + `Bash` akzeptabel? | **Ja, Persona bleibt unverändert.** `documenter` bleibt Referenzrolle; `agents/1-generic/documenter.md` wird **nicht** geändert (weder Persona-Text noch `tools:`). Der Grant wird im `AUTO_COMMIT_BLOCK` ausdrücklich als **Commit-Recht** ausgewiesen und in der Doku erklärt. Byte-Golden für Nicht-Grant-Rollen bleibt unverändert. | §3.4, §4.5 (Block), §7.1, §10 (N-9) |
| **D17** | OQ-1 — Auch `delegate`/`notify`/`none` akzeptieren (Revoke)? | **Nein, nur geben.** Schema-Enum = `["direct"]`. Entzug ausschließlich über (a) Entfernen der Rolle aus `roles:` oder (b) Entfernen des Override-Keys. Das Reason-Literal `grant withdrawn` bleibt **ausschließlich** an (a) gebunden; (b) ergibt `no Bash`. | §3.1, §3.2 (Nr. 6), §3.5, §4.1, §4.4, §5 (Nr. 1), §10 (N-8) |
| **D18** | OQ-2 — Gibt es eine kommando-genaue Bash-Permission? | **Nein.** Grant = **vollständige Shell**; die Doku sagt das ausdrücklich (keine „nur `git`"-Aussage). Der Guard blockt Sentinel-tragende Nicht-`git`-Kommandos; die Attributionslücke (Kommandos **ohne** Sentinel) wird als Grenze benannt und mit **#1210** verknüpft. Die Ack-Pflicht bleibt Pflicht. | §3.3.1, §4.5, §4.6, §5 (Nr. 6/10), §7.1, §8.1/§8.2 |
| **D19** | OQ-4 — Schrumpf-Warnung als CI-Gate? | **Nein, bleibt WARN.** Kein `--check`-/`--validate`-Gate, keine Exit-Code-Änderung; das exakte Log-Format bleibt gepinnt. Abstimmung mit **#1142** ist nur eine spätere Option. | §3.5, §4.6, §10 (AC-4) |
| **D20** | OQ-5 — Wirkt der Grant unter `suggest`? | **Nein.** `resolve_commit_grant` liefert für `suggest` `(derived, False)`; kein `Bash`-Render, keine Grant-Zeile, kein Sentinel. Sichtbarkeit in `eligible_roles`/Artefakt bleibt (Capability, nicht Mode). | §3.3, §4.3 (Docstring), §4.5, §10 (N-5) |
| **D21** | OQ-6 — Grant auf hook-losem Provider im gemischten Set = ERROR? | **Nein, WARN je Provider.** Auf Providern mit aktivem Guard wird gerendert; auf den übrigen bleibt die abgeleitete Authority + WARN. ERROR nur, wenn der Grant auf **keinem** Ziel-Provider wirken kann. `--validate`-Findings entsprechend. | §3.3, §4.3, §4.6, §10 (N-4/N-6) |
| **D22** | OQ-P2 — Rolle nicht in `roles:` = Fehler? | **Nein, INFO.** `authority_override_notices` liefert die INFO-Zeile ``<role>=direct ignored — role is not active (not listed in `roles:` or dropped by the active set)`` (§4.6); ERROR bleibt ausschließlich für read-only/unbekannte Templates und nicht durchsetzbare Grants. | §3.6, §4.3, §10 (N-7) |
| **D23** | OQ-P3 — Skalar-Kurzform akzeptieren? | **Nein, nur Objektform mit Pflicht-Ack:** `{authority: direct, acknowledge_full_shell: true}`. Skalar-Kurzform wird **nicht** akzeptiert; fehlendes/falsches Ack = Violation + kein Grant. | §3.1, §4.1, §4.3, §10 (N-2) |

**Statuswirkung:** Die Entscheidungen ändern den `Status` **nicht** — die Spec bleibt `DRAFT`.
Sie entfernen die Eskalationsmarker aus §7.2 und binden sie an konkrete Abschnitte, damit Plan und
Implementierung nicht mehr auf eine Review-Runde warten müssen.

---

**Trace-Anker:** `spec-id: SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09`
**Status:** DRAFT — keine Freigabe, keine Umsetzung. Offene Fragen: keine (D16–D23 entschieden).
