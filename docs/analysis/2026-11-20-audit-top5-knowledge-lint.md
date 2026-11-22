# Knowledge-Lint Audit — PR 0.5 / P32 (Stufe A)

- **Datum:** 2026-11-20 · **REQ-ID:** PR 0.5 / P32 / E-06 · **Rolle:** `knowledge-linter` (read-only)
- **Branch:** `chore/audit-top5-reports` @ `94a740c5` (via `.git/HEAD` + `.git/refs/heads/...` verifiziert)
- **Roadmap:** `docs/plans/2026-11-15-master-roadmap.md` §3.1 PR 0.5 / §1 P32. Knowledge Engine bleibt AN (E-14, Z. 20/70/282) — keine Abschaltungsempfehlung. Toter Key `knowledge.schema-language` (Z. 131) ist P9/P5, kein Lint-Befund.
- **Scope:** `knowledge/wiki/index.md`, `knowledge/schema.md`, `knowledge/wiki/log.md`, alle Seiten in `knowledge/wiki/{concepts,entities,topics,sources,plans}/` (112 MD-Dateien: 55 Concepts, 7 Entities, 40 Topics, 6 Sources, 2 Plans + index/log). `knowledge/wiki/specs/` (schema.md:35) existiert nicht.

## Randbedingungen
Read-only — keine Wiki-Seite, kein Frontmatter, kein Index/Log verändert. Kein Full-Testlauf (G1 von USER 2026-11-20 übersprungen). Findings nur adressiert, nicht delegiert. Kein Commit/Push/PR/Issue, keine verbotenen MCP-Tools, kein Worktree/isolation-Flag.

## Gesamturteil
Content-Katalog vollständig, keine echt kaputten Cross-References. Ein **CRITICAL**-Befund, zwei **HIGH**-Befunde, ein **MEDIUM**-Befund erfordern Follow-up.

## 1. Widersprüche — MEDIUM/HIGH
- **C-01 HIGH:** `topics/se-workflow.md:14` „Aktuell aktiv (Stand 2026-06-20): 14 SE-Agenten-Templates" vs. `concepts/architecture-se-cascade.md:14` + `index.md:21` „seit 2026-09-03 deaktiviert (Issue #652)"; neuere Quelle (`architecture-se-cascade.md:6` = 2026-09-03). Review 2026-09-03 / Expiry: Statusänderung #652.
- **C-02 MEDIUM:** `concepts/se-cascade-optimization-339.md:44,501` „Keine Admin-UI im Repo" (Stand 2026-06-28) vs. `entities/admin-ui-reference.md:1-4`, `docs/plans/admin-server-split-backlog.md`.
- **C-03 MEDIUM:** `concepts/dynamic-model-presets.md:4` „Status: Umgesetzt" vs. `index.md:40` `status:planned`.
- **C-04 MEDIUM:** `topics/agent-isolation.md:18-27` empfiehlt `isolation: worktree` vs. `AGENTS.md` „No Worktree Isolation" (Anti-Pattern).
- **C-05 LOW:** `knowledge/schema.md:11` „84 files" vs. `log.md:21` „82" vs. `log.md:27` „107 OKF-Dokumente".

## 2. Veraltete Claims — HIGH
- **S-01 HIGH:** `concepts/architecture.md:9,14` selbst als stale markiert („reviewed: 2026-07-20"), `index.md:24` `status:stale-upstream`, `log.md:30`. Review 2026-07-20 / Expiry: >4 Monate, Config nun `.meta-config/project.yaml` + `config/*.yaml`.
- **S-02 MEDIUM:** Großteil Timestamp 2026-07-27 (Belege `sources/*.md:6`, `topics/template-gap-analysis.md:6`, `concepts/singleton-orchestrator-architecture.md:6`); Ausnahme `core-principle-pal-variables.md:6` = 2026-11-11.
- **S-03 MEDIUM:** `topics/template-gap-analysis.md:3,10` „Stand 2026-04-01", Vergleich gegen skplugin/skherointroduce. Review 2026-04-01.
- **S-04 MEDIUM:** `concepts/singleton-orchestrator-architecture.md:17`, `index.md:60` — eigene if/elif-Beispiele überholt seit #625–#638. Review 2026-09-03.
- **S-05 MEDIUM:** Claim-Expiry dokumentiert (`concepts/knowledge-engine-concept.md:1706`), aber kein `review_date`/`expires` im Wiki-Frontmatter (0 Treffer).

## 3. Orphans — MEDIUM
- **O-01 MEDIUM:** `knowledge/wiki/log.md` — 0 Inbound-Links, nicht in `index.md` verlinkt → Orphan nach Wikipedia-Kriterium. Adoption via `knowledge-gardener`.
- **O-02 LOW:** `knowledge/schema.md` nicht verlinkt (außerhalb Wiki-Index).
- Positiv: alle 110 Content-Seiten in `index.md` → keine inhaltlichen Orphans.

## 4. Fehlende Concepts — MEDIUM
- **K-01 MEDIUM:** `feature-lifecycle`-Pipeline ohne eigene Seite — `concepts/architecture-agent-roles.md:100,104`, `concepts/architecture-dev-workflow.md:46,48,56,63,66`, `index.md:15-16`. Stub vorschlagen.
- **K-02 LOW:** `.meta-config/context-hashes.json` ohne Seite — `core-principle-submodule-protection.md:44,71,86,88`, `provider-agnostic-policy.md:14,51,56`.

## 5. Broken Links — HIGH (Status: clean)
- **L-01 HIGH (clean):** 153 Index-Links (55/7/40/45/6) + alle Cross-References geprüft — **alle Ziele existieren**. `../../../ARCHITECTURE.md` (8×), `../../../CLAUDE.md` (`topics/agent-memory.md:240`, `topics/rules.md:163`), `agents/1-generic/` (`se-cascade-optimization-339.md:15`) vorhanden.
- **L-02 LOW:** 4 Platzhalter-Links `concepts/knowledge-engine-concept.md:178,564,872,877` (`related.md`, `entity-name.md`, `entity-a.md`, `attention.md`) sind Beispiele → als Code markieren. Link-Rot: bei externen Brüchen Wayback/Replacement-Target benennen (derzeit keine).

## 6. Datenlücken — LOW
- **D-01 LOW:** `concepts/architecture-external-skills.md:4`, `concepts/architecture-versioning.md:4` — `description:` = `title:`.
- **D-02 LOW:** `topics/template-gap-analysis.md:3,10` — veraltete Vergleichsbasis (siehe S-03).

## 7. `type`-Frontmatter (OKF §4.1) — CRITICAL
- **F-01 CRITICAL:** `knowledge/wiki/index.md:1` beginnt mit `# Knowledge Index` — **kein YAML-Frontmatter, kein `type:`**. OKF §4.1 REQUIRED; Referenz `concepts/knowledge-engine-concept.md:862` definiert `type: Index`. Sofort an `knowledge-gardener`.
- Positiv: alle 110 Content-Seiten + `log.md:3` haben `type:`.
- **F-02 MEDIUM:** `log.md:3` `type: "Guide"` vs. OKF `type: Log` (`knowledge-engine-concept.md:892`); `knowledge/schema.md:27-35` listet weder `Index` noch `Log` → Entscheidung `knowledge-curator`.

## 8. Recommended Frontmatter — LOW
- **R-01 LOW:** `plans/am-issue-456-remote-admin-auth.md:1-9`, `plans/am-fix-planner-pipeline-ghost-entries.md:1-9` — `type` + `title`, kein `description`.
- **R-02 LOW:** siehe D-01.

## 9. `index.md` veraltet (OKF §6) — MEDIUM
- **I-01 MEDIUM:** Plan-Katalog (`index.md:118-172`, Stand 2026-11-09 laut `log.md:31-32`, 45 Einträge) übersieht post-2026-11-09-Pläne, z. B. `docs/plans/2026-11-14-audit-top5-execution-plan.md`, `2026-11-15-master-roadmap.md`, `2026-11-16-bug-backlog-working-plan.md`, `2026-11-19-worker-control-capability-plan.md`, `2026-11-09-artifact-locations-matrix-plan.md`. Ausschlussregeln `index.md:118` beachten → `knowledge-indexer`.
- Positiv: 55/55 Concepts, 40/40 Topics, 7/7 Entities, 6/6 Sources, 2/2 Wiki-Pläne indiziert.
- **I-02 LOW:** `index.md:3` erwähnt nur concepts/entities/topics, nicht Plans/Sources.

## 10. `log.md`-Inkonsistenzen (OKF §7) — LOW
- **G-01 LOW:** `log.md:5` `timestamp: "2026-11-09"` < letzter Eintrag `log.md:33` `2026-11-12` → `knowledge-indexer`.
- Positiv: alle in `log.md:21-33` genannten Seiten existieren; keine Einträge ohne Korrespondenz.

## Priorisierte Remediation (E-14: Knowledge Engine bleibt AN)
| Prio | IDs | Maßnahme | Adressat |
|---|---|---|---|
| P0 | F-01 | `type: Index` + title/description/timestamp in `index.md` | `knowledge-gardener` |
| P1 | C-01, S-01, C-02, C-03, C-04 | Claims korrigieren, je `review_date` + `expiry_reason` | `knowledge-ingestor` |
| P1 | I-01 | Plan-Katalog nachziehen (Ausschlussregeln prüfen) | `knowledge-indexer` |
| P2 | O-01, K-01, F-02, S-05 | log.md adoptieren, Stub, Schema-Entscheidung, Review-Felder | `knowledge-gardener`/`knowledge-curator` |
| P3 | R-01, D-01, D-02, S-02–S-04, L-02, C-05, G-01, O-02, K-02, I-02 | Metadata, Platzhalter, Zählungen, Log-Timestamp | alle drei |

Keine Maßnahme schränkt die Knowledge Engine ein (E-14).

## Abschlussvermerk
Read-only: keine Wiki-Seite verändert, kein Full-Testlauf (G1 skipped). Kein Commit/Push/PR/Issue, keine verbotenen MCP-Tools, kein Worktree/isolation-Flag.

STATUS: done
RESULT: Knowledge-Lint-Audit vollständig durchgeführt (alle 10 Checks); schwerwiegendster Befund ist CRITICAL: `index.md` besitzt kein `type`-Frontmatter (OKF §4.1), dazu 2 HIGH-Befunde (stale `architecture.md`, SE-Status-Widerspruch) und MEDIUM Plan-Katalog-Staleness. Kein Wiki-File verändert, kein Full-Testlauf.
