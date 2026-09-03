# Detail-Audit: System, Templates, Doku, Config — 2026-09-03

## STATUS

**done** — Audit, keine Umsetzung. Empfehlungen in §6 sind Vorschläge, keine Issues (noch nicht gefiled).

## Scope

Nachfolge-Audit zu `audit-2026-09-system-concept.md` (2026-09-02), das Agent-Templates und Doku bewusst ausgeschlossen hatte. Dieses Mal **ohne Ausschluss** — breiter und tiefer, nach vollständigem Abschluss der Provider-Agnostik-Kampagne (Waves A-D, #625-#633, #638 — main sauber, Stand 2026-09-03).

**Methode:** 4 parallele Recherche-Forks (rein lesend, kein Schreibzugriff):
1. Agent-Templates (`agents/1-generic/`, `agents/2-platform/`)
2. Dokumentation (`docs/`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`)
3. Config/Presets, Admin-Server, Test-Suite-Gesundheit
4. Knowledge-Engine, SE-Cascade, Feature-Bloat (YAGNI-Brille)

---

## 1. Gesamturteil (TL;DR)

- **Zwei echte Wahrheits-Widersprüche gefunden**, beide mit direktem Irreführungspotenzial für künftige Agenten-Sessions: `config/prompt-modes.yaml` vs. `docs/architecture/prompt-modernization.md` (Prompt-Schema-Status), und `docs/architecture/02-sync-flow.md` (beschreibt Config-Dateien, die es nicht mehr gibt).
- **Composition-Anti-Pattern lebt in `2-platform` weiter:** 12 von 17 Dateien nutzen `based-on` nur als Herkunftsangabe, der Body ist Full-Replacement — genau das Muster, das für `developer.md` (#560) bereits einmal gefixt wurde, hier aber breitflächig unadressiert.
- **Die wiederkehrende Python-3.9-Bug-Klasse (2x in dieser Kampagne) hat weiterhin keinen präventiven Schutz** — CI fängt sie zuverlässig ab, aber erst nach dem Push, nicht vorher.
- **Versionsdrift in Nutzer-sichtbarer Doku:** README-Badge (`0.92.0`) und CHANGELOG (letzter Eintrag `0.1.0`/April) liegen weit hinter `VERSION` (`0.101.0-beta.4`) und main zurück — beide Refactoring-Kampagnen (August-Roadmap, Provider-Agnostik) sind nirgends changelog-dokumentiert.
- **Kein Bloat-Fund von Substanz:** Knowledge-Engine, SE-Cascade (13 Rollen, deaktiviert), DoD-Presets, MCP-Registry sind alle plausibel begründete, bewusst vorbereitete oder bewusst deaktivierte Infrastruktur — kein YAGNI-Streichkandidat, aber SE-Cascade und das Knowledge-Wiki sollten der User explizit bestätigen/auffrischen.
- **Test-Lücke:** 8 von 9 in dieser Kampagne neu extrahierten `scripts/lib`-Modulen haben kein eigenes `test_*.py`.

---

## 2. Agent-Templates

### 2.1 Prompt-Mode-Widerspruch (P1)

- `config/prompt-modes.yaml`: `default: legacy`, `modern-templates: [developer, orchestrator]`, setzt `agents/1-generic-modern/` voraus.
- `docs/architecture/prompt-modernization.md`: behauptet, das 6-Block-XML-Schema sei "der alleinige Standard", der frühere Dual-Tree-Ansatz sei "vollständig aufgelöst".
- Realität: `agents/1-generic-modern/` **existiert nicht**. Alle gesampelten `1-generic/*.md` nutzen bereits nativ XML.
- → `prompt-modes.yaml` ist totes Config-Fragment einer abgeschlossenen Migration; widerspricht der eigenen Architektur-Doku, wurde nicht aufgeräumt.

### 2.2 Struktur-Konsistenz

- 4 Templates fehlt `<output_contract>`: `backend-reviewer.md`, `database-reviewer.md`, `frontend-reviewer.md`, `ui-reviewer.md` — genau das Muster, das als "in Wave 9 gefixt" galt, ist es bei diesen 4 nicht.
- **~13 `se-*.md`-Dateien (SE-Kaskade) nutzen gar kein XML-Schema**, klassisches Markdown+Prosa — direkter Widerspruch zur "alleiniger Standard"-Aussage aus 2.1.
- Einzelne bewusste Ausreißer (Extra-Blöcke bei `bug-feature-analyzer`, `incident-responder`, `principal-developer`; `intern-developer` komplett anders — Gag-Agent) sind vermutlich beabsichtigt.

### 2.3 Composition-Anti-Pattern in `2-platform` (P1)

- Nur 5 von 17 Dateien (alle `hacs-*.md`) nutzen echte `extends`+`patches`-Composition.
- **12 von 17** nutzen `based-on` nur als Herkunftsangabe, Body komplett neu geschrieben (Full-Replacement) — u.a. `agent-meta-developer.md` (210 Z.), `homeassistant-documenter.md` (262 Z.), `sharkord-release.md` (271 Z., längste 2-platform-Datei).
- Risiko: ändert sich das `1-generic`-Basis-Template, muss bei diesen 12 Dateien manuell nachgezogen werden — keine strukturelle Garantie. Historisch bereits einmal für `developer.md` allein gefixt (#560), hier großflächig nicht.

### 2.4 Sonstiges

- Tool-Privilege-Lint meldet aktuell 0 Treffer (keine akute Verletzung).
- Orphan-Check (Templates ohne `role-defaults.yaml`-Eintrag) per Grep nicht belastbar — siehe §4 (Fork 4 fand per YAML-Parse nur `provider-expert` als echten Kandidaten, vermutlich legitime Basis-Vorlage für `*-expert`-Rollen).

---

## 3. Dokumentation

### 3.1 `docs/architecture/02-sync-flow.md` — massiv veraltet (P1)

- Referenziert `agent-meta.config.json`/`.yaml`, `roles.config.yaml`, `external-skills.config.yaml` — existieren nicht mehr. Aktuell: `.meta-config/project.yaml` + `config/ai-providers.yaml` etc.
- Überschrift "Neue Features in v0.17.0" bei aktueller `VERSION` `0.101.0-beta.4`. Zuletzt geändert 2026-04-17.
- `01-layer-model.md` (29.08.) und `03-agent-roles.md` (02.09.) sind aktuell. `04-dev-workflow.md`, `05-external-skills.md`, `06-versioning.md`, `07-se-cascade.md` seit April/Juni/August unverändert, keine harten Widersprüche gefunden, aber ungeprüft auf Detail-Drift.

### 3.2 README.md — Versionsdrift (P1)

- Versions-Badge zeigt `0.92.0`, Quickstart nutzt `git checkout v0.92.0` — `VERSION`-Datei: `0.101.0-beta.4`. Datums-Badge `2026-08-07` (heute: 2026-09-03).
- Provider-Liste (6) korrekt. Agenten-Summe in README-Tabellen (77) weicht leicht von `agents/1-generic/*.md | wc -l` (76 Rollen + 1 `provider-expert`) ab — minor.

### 3.3 CHANGELOG.md — massiv hinter main (P2)

- Letzter Eintrag `[0.1.0] — 2026-04-01`. Weder August-Roadmap (10 Waves) noch Provider-Agnostik-Kampagne (4 Waves) dort verzeichnet, obwohl `VERSION` längst bei `0.101.0-beta.4`.

### 3.4 `docs/plans/` — kein Archivierungskonzept (P2)

- 12 Dateien, Reports (abgeschlossen, rückblickend) und Pläne (aktiv, vorwärtsgerichtet) liegen flach im selben Ordner, wachsend mit jeder Session. Kein `archive/`-Unterordner.

### 3.5 CODEBASE_OVERVIEW.md — aktuell

- Zuletzt 2026-09-02 aktualisiert, spiegelt neue Module (`subagent_dispatch`-Capability etc.) korrekt wider. Kein Befund.

### 3.6 Redundanz-Check — kein Befund

- Keine inhaltliche Dopplung zwischen `docs/architecture/*.md` und `.claude/rules/*.md` gefunden (z.B. Guard-Terminologie existiert nur in `rules/branch-guard.md`).

---

## 4. Config, Admin-Server, Test-Suite

### 4.1 Python-3.9-Bug-Klasse — kein präventiver Schutz (P1)

- Aktuell 100 % Abdeckung (jede Datei mit `X | Y`-Syntax hat `from __future__ import annotations`, verifiziert), aber **kein AST-Lint/pre-commit-Hook** existiert, der das systematisch für neue Module erzwingt. `.pre-commit-config.yaml` fehlt komplett; `scripts/lib/consistency/*.py` hat keinen entsprechenden Check.
- CI (`.github/workflows/orchestration-test.yml`) läuft korrekt bei jedem PR mit Matrix 3.9/3.11/3.12 — die zwei Vorfälle dieser Kampagne wurden also von CI erkannt, aber erst **nach** dem Merge bemerkt (reaktive Diagnose statt PR-Gate-Blockade vor Merge).

### 4.2 Admin-Server — kein akuter Befund

- 5330 Zeilen (Ausreißer, aber CLI-Skript, nicht der 600-Zeilen-`scripts/lib`-Konvention unterworfen). `RoleDefaultsEditor` (#611-Fix) wirkt jetzt generisch genug (saubere Liste/Dict-Helper-Trennung), nicht nur für die zwei ursprünglichen Testfälle gepatcht.

### 4.3 Config-Presets — kein Befund

- `sync.py --validate` sauber (`[PASS]`), `provider_registry_completeness` (#625) meldet aktuell keine Lücken über alle 6 Provider.

### 4.4 Test-Lücke bei neuen Modulen (P2)

- 8 von 9 in dieser Kampagne neu extrahierten Modulen ohne eigenes `test_*.py`: `mcp_registry.py`, `hook_plugins.py`, `hook_drift.py`, `config_audit_providers.py`, `config_audit_apply.py`, `json_persistence.py`, `variables.py`, `agent_sync.py`. Nur `frontmatter.py` hat `test_frontmatter_canonical.py`. Vermutlich indirekt über Integrationstests mitgetestet, aber keine gezielte Unit-Abdeckung.

### 4.5 Selbst-Review Wave C/D — sauber

- `provider_transform.py`: 0 hardcodierte Provider-Namen, `_apply_agent_transform`-Dispatcher wirklich generisch. `hooks.py`/`hook_plugins.py`-Split sauber unidirektional.

---

## 5. Knowledge-Engine, SE-Cascade, Feature-Bloat

- **Knowledge-Wiki veraltet (P2):** `knowledge/wiki/` ist reale, gepflegte Selbst-Introspektion (agent-meta ingested eigene Doku/Historie), aber Stand 10.-11.08 — **vor** der großen Refactoring-Kampagne. Konzeptseiten wie `concepts/architecture-se-cascade.md`/`concepts/prompt-modernization.md` spiegeln vermutlich nicht mehr den aktuellen Code-Stand.
- **SE-Cascade — vollständig gebaut, aber deaktiviert:** 13 `se-*`-Rollen + `scripts/run-cascade.py` + eigene Doku, `quality-pipelines.overrides.se-cascade.enabled: false` in `.meta-config/project.yaml`. Kein Bloat per se, aber User-Bestätigung sinnvoll: reaktivieren geplant oder Archivierungskandidat?
- **DoD-Presets:** 3 definiert (`full`, `standard`, `rapid-prototyping`), nur einer aktiv, keine Testabdeckung — geringe Kosten, kein Streichkandidat.
- **Agenten-Inventar:** 76 Rollen, 73 automatisch via `intent_keywords` erreichbar. 4 manuell-only (`orchestrator`, `intern-developer`, `principal-developer`, `openscad-developer`) — alle selbst-dokumentiert als bewusst manuell, kein totes Rollen-Set.
- **MCP-/External-Tools-Registry:** minimal (1 Eintrag: `graphify`), alle Konsumenten vorhanden, kein Bloat.

---

## 6. Priorisierte Empfehlungen

**P1**
1. `config/prompt-modes.yaml` bereinigen (totes Legacy-Fragment, referenziert nicht-existentes `agents/1-generic-modern/`) — oder `docs/architecture/prompt-modernization.md` korrigieren, je nachdem was stimmt.
2. Full-Replacement-Overrides in `2-platform` (12 von 17 Dateien) auf `extends`+`patches` migrieren, analog zu den 5 `hacs-*`-Dateien.
3. `docs/architecture/02-sync-flow.md` neu schreiben — beschreibt nicht mehr existierende Config-Dateien, aktiv irreführend.
4. README-Versions-Badge + Checkout-Beispiel an `VERSION`-Datei koppeln (Platzhalter oder CI-Check).
5. Präventiver AST-Lint/pre-commit-Check gegen `X | Y`-Syntax ohne `from __future__ import annotations` in `scripts/lib/*.py` — verhindert 3. Wiederholung dieser Bug-Klasse.

**P2**
6. CHANGELOG.md nachziehen (mind. zusammenfassende Einträge für beide Refactoring-Kampagnen).
7. `docs/plans/`-Archivierungskonvention einführen (`archive/`-Unterordner für abgeschlossene Reports).
8. `<output_contract>` bei den 4 verbliebenen Reviewer-Templates nachziehen.
9. Fehlende Unit-Tests für neue Wave-6-D-Module nachziehen (mind. `hook_drift.py`, `mcp_registry.py`).
10. Knowledge-Wiki via `knowledge-migrator`/`knowledge-gardener` re-ingesten oder explizit als "Snapshot, kein Live-Spiegel" kennzeichnen.
11. SE-Cascade-Status mit User klären (reaktivieren vs. archivieren).

**P3**
12. Klären, ob `se-*.md` bewusst außerhalb des XML-Standards steht — dann explizit in `prompt-modernization.md` als Ausnahme dokumentieren statt "alleiniger Standard" zu behaupten.
13. `provider-expert`-Template-Zweck dokumentieren (kein `role-defaults.yaml`-Eintrag, vermutlich legitime Basis-Vorlage).
14. Agenten-Zahl in README (77 vs. 76+1) stichprobenartig verifizieren.
15. `admin-server.py` (5330 Zeilen) als Kandidat für künftigen Split-Wave vormerken.
