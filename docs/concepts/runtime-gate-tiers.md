# Konzept — Runtime-Gate-Tiers des CRITICAL GATE

- **Status:** Accepted (Phase 0 implementiert; End-to-End-Verifikation in Task 7; Phase 1 zurückgestellt)
- **Spec:** [`../specs/2026-09-13-opencode-runtime-gate-design.md`](../specs/2026-09-13-opencode-runtime-gate-design.md)
  (`spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`, Status APPROVED)
- **Plan:** [`../plans/2026-09-13-opencode-runtime-gate.md`](../plans/2026-09-13-opencode-runtime-gate.md)
- **Gap-Kontext:** [`../process-capability-gaps.md`](../process-capability-gaps.md)
- **Betroffener Bereich:** Rules-/Context-Rendering, Consistency-Check, Permission-Merge
- **Nicht in diesem Dokument:** Implementierung, Provider-Logik (`if provider == …`), Rollen-Routen, Modellnamen
- **Terminologie:** „Convention boundary" / „security boundary" wird exakt wie in
  [`../../.claude/rules/branch-guard.md`](../../.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary)
  definiert verwendet; die zentrale Definition wird hier nicht wiederholt.

---

## 1. Warum Tier-Semantik?

Der `# CRITICAL GATE` („MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.")
ist nur so stark wie das Runtime, das ihn auf dem aktiven Provider stützt. Früher war
der Satz unbedingt — auch auf Providern ohne Runtime-Gate. Diese Doku beschreibt die
ehrliche, gestufte Zusage: Jeder Provider trägt genau das Tier, das seine
**deklarierte** Capability stützt.

Der Gate bleibt insgesamt eine **Convention boundary**, ausdrücklich **keine
security boundary**: Ein Modell kann das Plugin deaktivieren, `opencode.json`
editieren oder Delegation nur behaupten. Das ist eine bewusste, dokumentierte Grenze
(analog `orchestrator-guard.sh`), kein behebbarer Bug.

## 2. Die vier Tiers

Kanonische Vokabel: `scripts/lib/runtime_gate.py::RUNTIME_GATE_TIERS =
("hook", "plugin", "permission", "advisory")`.

| Tier | Runtime-Zusage | Stand |
|---|---|---|
| `hook` | Verifizierter PreToolUse-Hook-Vertrag: das Runtime blockiert den Tool-Call (`GATE_ENFORCED`). | Phase 0 aktiv, wo `hooks: true` + verifiziertes `hook_protocol` deklariert ist. |
| `plugin` | Native Plugin-Tier; Artefakt läuft im Modus `observe` (nur Logging). | **Phase 1, DEFERRED**, capability-gated; erst nach der Real-Repo-Verifikation (P6). In Phase 0 deklariert kein Provider `runtime_gate: plugin`. |
| `permission` | Native Permission-Schicht blockiert Main-Chat-Writes (A2-Root-Deny). **PARTIAL**: keine Delegations-Provenienz. | Phase 0 (aktueller Status des permission-fähigen Providers). |
| `advisory` | Rein prompt-basiert, ohne Runtime-Gate. | Fail-safe-Default für unbekannte/fehlende Konfiguration. |

- `advisory` schreibt **nie** einen Permission-Eintrag und deployt **nie** ein Plugin.
- `plugin` ist ohne `has_plugins`/verifiziertes `plugin_protocol` unerreichbar;
  `MODE=enforce` ist zusätzlich gesperrt (siehe §7).

## 3. Resolver-Präzedenz & Fail-safe

Einzige Wahrheitsquelle:
`scripts/lib/providers.py::provider_runtime_gate_tier(pc, capabilities)`.
Zwei Registry-Split (D-C1): Maschinen-Flags kommen aus `config/ai-providers.yaml`
(`pc`), die deklarierte Tier aus `config/provider-capabilities.yaml` (`capabilities`).

Präzedenz (first match wins):

1. `provider_hooks_supported(pc)` → `hook`
2. `provider_runtime_gate_supported(pc)` (`has_plugins` + `plugin_protocol`) → `plugin`
3. `capabilities.runtime_gate == "permission"` → `permission`
4. sonst → `advisory`

Der Resolver **wirft nie**, ruft nie `sys.exit` und fällt nie auf eine
Hook-/Provider-Wahrheit zurück. Unbekannter/fehlender Provider, `None`/Nicht-Mapping
`pc`, absentes `runtime_gate` oder eine unlesbare Registry → `advisory`.

`config/provider-capabilities.yaml` deklariert `runtime_gate` explizit je Provider
(Pflicht wie bei `commands`); die Sync-Time-Invariante macht ein fehlendes Key zum
Testfehler, das Runtime-Verhalten bleibt trotzdem fail-safe `advisory`.

## 4. Die PARTIAL-Grenze der Tier `permission` (Phase 0)

A2 schreibt unter effektivem `strict` einen Main-Chat-Deny in der **Mapping-Form**
innerhalb der bestehenden Permission-Familien:

```json
{"edit": {"**": "deny"}, "bash": {"**": "deny"}}
```

- Der Deny blockiert Main-Chat-Writes/Bash in der **Main-Session**.
- **Nicht erzwungen ist die Delegations-Provenienz**: Eine delegierte Child-Session ist
  von der Main-Session nicht unterscheidbar.
- Die Child-Session-Propagation (`deriveSubagentSessionPermission`, Issue **#765**) ist
  **unverifiziert**. Die Tier `permission` darf deshalb **niemals als vollständig
  erzwungen** beschrieben werden — sie ist und bleibt PARTIAL.

Offene Phase-0-Risiken (dokumentiert, nicht versteckt):

- **AN-6 / OQ-3:** Ob Agent-Frontmatter-Permissions den Root-Deny für
  `orchestrator`/`git` übersteuern, ist eine Hypothese. Zeigt die Real-Repo-Prüfung,
  dass der Root-Deny diese Rollen blockiert, wird A2 auf feinere `bash`/`edit`-Globs
  verengt — niemals auf einen gröberen Block.
- Solange diese Risiken offen sind, trägt der benachbarte Tier-Hinweis in
  `rules/1-generic/a2a-delegation-gates.md` die Grenze, nicht eine Abschwächung des
  Gate-Satzes.

## 5. Rendering: gestufte Zusage

`providers.runtime_gate_vars(pc, capabilities, config)` liefert das String-Bundle
`ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`,
`RUNTIME_GATE_PLUGIN_MODE`. Es wird an beiden Renderer-Seams in die
`provider_variables` injiziert (Context und Rules).

- `GATE_ENFORCED` = `true` für `hook` (Phase 0) und `plugin` (Phase 1, observe).
- `GATE_PARTIAL` = `true` nur für `permission`.
- `GATE_ADVISORY` = `true` nur für `advisory`.

`rules/1-generic/use-orchestrator.md` rendert innerhalb `{{#if ORCH_MODE_STRICT}}`
genau einen der drei zueinander exklusiven Blöcke. Die `GATE_ENFORCED`-Variante
reproduziert den bisherigen Strict-Wortlaut **verbatim** (`# CRITICAL GATE` +
`… ALLES -> \`orchestrator\`. Keine Ausnahmen.`), sodass die Ausgabe
Hook-fähiger Provider byte-identisch bleibt (F-05). Die Provenienz trägt der
Tier-Hinweis in `rules/1-generic/a2a-delegation-gates.md` (mit `{{ENFORCEMENT_TIER}}`
und Verweis auf „Bekannte Grenzen").

## 6. Consistency-Severity (A4)

`scripts/lib/consistency/orchestrator_strict.py::check_orchestrator_strict_hook_support`
leitet die Severity aus derselben Tier ab (Check-ID unverändert
`orchestrator-strict.no-hook-support`):

| Tier | Finding |
|---|---|
| `hook` / `plugin` | kein Finding |
| `permission` | INFO („partial enforcement, no provenance") |
| `advisory` | WARNING (Default); ERROR nur bei `orchestrator.require-runtime-gate: true` |

`orchestrator.require-runtime-gate` ist ein Boolean-Sibling-Key (Default `false`,
D-C2). `runtime-gate.plugin-mode` (`enum: [observe, enforce]`, Default `observe`) ist
der Phase-1-Schema-Key (IC-16) und beeinflusst das Phase-0-Rendering nicht.

## 7. Phase-1-Vorbehalt (P6, #765)

Die Plugin-Tier ist bewusst zurückgestellt und capability-gated:

- Der Plugin-Generator ist Phase 1 (DEFERRED); das Artefakt ist `MODE=observe`.
- `runtime_gate: plugin`, `has_plugins: true`, `MODE=enforce` und der Tier-Flip sind
  erst nach bestandener Real-Repo-Verifikation (P6) freigeschaltet.
- Kein Provider darf vorher `plugin` deklarieren; es wird nie „vollständig erzwungen"
  behauptet.

## 8. #747-Avoidance

A2 liest und schreibt `opencode.json` ausschließlich über den bestehenden
Merge-Pfad in `scripts/lib/isolation.py` (`_read_json_safe` / `write_checked`) —
**nie** über den create-only Settings-Initializer
`context._init_provider_settings_json` (#747). Es wird kein neuer Root-Key erzwungen.

Der geteilte Managed-State `.opencode/agent-meta-state.json` ist namespaced
(`isolation-deny` und `runtime-gate-deny`); der A2-Writer ersetzt per
Read-Modify-Write nur seinen Namespace, zeichnet einen vorbestehenden User-Wert am
Glob `"**"` auf und stellt ihn bei einer `strict` → non-`strict`-Transition exakt
wieder her. Wiederholte Strict-Syncs sind idempotent (byte-identisch). Der
A2-Dispatch keyt auf `provider_runtime_gate_tier(...) == "permission"` und läuft
auch für Single-Provider-Projekte (nicht am ≥2-Provider-Guard der Isolation
gekoppelt).

## 9. Referenzen

- `scripts/lib/runtime_gate.py::RUNTIME_GATE_TIERS` — Tier-Vokabel (Seam).
- `scripts/lib/providers.py::provider_runtime_gate_tier` / `::runtime_gate_vars` — Resolver + Bundle.
- `config/provider-capabilities.yaml:capabilities.<provider>.runtime_gate` — deklarierte Tier.
- `scripts/lib/isolation.py::_sync_opencode_runtime_gate` — A2-Root-Deny/Merge.
- `scripts/lib/consistency/orchestrator_strict.py` — tier-abgeleitete Severity.
- `rules/1-generic/use-orchestrator.md`, `rules/1-generic/a2a-delegation-gates.md` — gestufte Zusage.
