# Memory Index

- [#643 2-platform extends migration](issue-643-platform-extends-migration.md) — DONE: 5 migrated / 8 skipped; needed 2 engine fixes (standalone XML anchor + override-order merge); NOT committed
- [Wave C: provider_transform data-driven (#629)](wave-c-provider-transform-data-driven-629.md) — DONE: 6-way elif → agent-transform YAML spec; all 6 providers byte-identical, suite green, NOT committed

- [Model-ID Canonical Source](model-id-canonical-source.md) — platform.claude.com is authoritative; fix/admin-ui-model-sync partially ported (dc5205b), merge will conflict
- [Viz Audit Findings](viz-audit-findings.md) — 3 verified broken paths: delegate_out mismatch, viz-server.py import, literal \n injection
- [SE-Kaskade Status](se-cascade-status.md) — Konzept v1.0 unimplementiert; SE_ENABLED-Scoping-Bug gefixt (0123655, Ursprung 4e36c10)
- [Dual Template Tree (Modern)](dual-template-tree-modern.md) — 1-generic/ Edits greifen NICHT für agent-meta selbst; 1-generic-modern/ überschreibt; beide Bäume pflegen
- [Orchestrator-Table Check False-Positive](orchestrator-table-check-false-positive.md) — crossrefs.orchestrator-table-incomplete ist Placeholder-bedingter False-Positive; NICHT durch Edit an orchestrator.md fixen
- [Reflection-Overrides Dead Code](reflection-overrides-deadcode.md) — reflection-pairs.overrides wirken NICHT (reflection.py nicht in config.py verdrahtet); quality-pipelines.overrides wirken dagegen
- [Tier-Resolution Silent-Empty](tier-resolution-missing-key-silent-empty.md) — resolve_model gibt "" zurück wenn Tier-Key im aktiven Preset fehlt; neue Tiers in ALLE Presets + Provider-Blöcke eintragen
- [Multi-Provider 3-File-Invariante](multi-provider-three-file-invariant.md) — Provider aus ai-providers.yaml muss auch in capabilities/bootstrap/delegation-syntax stehen, sonst Silent-Downgrade (PAL_* gestrippt); Copilot = konservatives Referenz-Pattern
- [Neuer _BLOCK-Platzhalter: 2 versteckte Kopplungen](new-block-placeholder-coupling.md) — build_variables _BLOCK-Var braucht auch Eintrag in consistency/placeholders.py _BUILTIN_VARS + standalone.py Fallback
- [Admin-Server God-Object-Split (#572)](admin-server-god-object-split.md) — DONE: alle 6 Services (Auth/Audit/Template/Pipeline/Reflection/Models) + RoleDefaultsEditor + ServiceContext; Delegation-Pattern, Tests unverändert grün
- [Admin-Server Test-Run Gotcha](admin-server-test-run-gotcha.md) — Tests brauchen -p no:homeassistant (OpenSSL `lib` kollidiert mit scripts/lib); full ~6.5min, admin-only ~0.4s
- [Wave 6 sync-core Split](wave6-sync-core-split.md) — #565 variables.py + #561 agents.py-Split (frontmatter/provider_transform/agent_sync) DONE, SCC 8→3; #563 DONE (Dispatch-Table+_SyncContext, main 490→10 Z., 4/5 Kriterien, Subparser-Kriterium unmöglich ohne CLI-Bruch)
