# Konzept — Runtime-Gate-Tiers des CRITICAL GATE

- **Status:** Accepted (Phase 0 implementiert und abgenommen; **Phase 1 / Plugin-Tier für die Opencode-v2-Surface geliefert (C3, Modus `observe`)**; `MODE=enforce` bleibt durch P6 gesperrt; v1 bleibt `permission`)
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
| `plugin` | Native Plugin-Tier; das Artefakt ist ausschließlich auf den Modus `observe` (nur Logging) ausgelegt. | **Seit C3 geliefert für Opencode v2:** aufgelöst über die Daten `surface-has-plugins.v2: true` und `surface-plugin-protocols.v2: opencode-plugin-v2-js`; v1 behält das statische `has_plugins: false` und bleibt `permission`. `MODE=enforce` bleibt gesperrt, bis P6 bestanden ist. |
| `permission` | Native Permission-Schicht blockiert Main-Chat-Writes (A2-Root-Deny). **PARTIAL**: keine Delegations-Provenienz. | Phase 0 (aktueller Status des permission-fähigen Providers), **best-effort — nicht garantiert**. |
| `advisory` | Rein prompt-basiert, ohne Runtime-Gate. | Fail-safe-Default für unbekannte/fehlende Konfiguration. |

- `advisory` schreibt **nie** einen Permission-Eintrag und deployt **nie** ein Plugin.
- `plugin` ist nur über aufgelöste Daten erreichbar: truthy `has_plugins` **und** ein
  `plugin_protocol` aus `SUPPORTED_PLUGIN_PROTOCOLS`. Das statische `has_plugins: false` bleibt,
  damit v1 nie `plugin` wird; Opencode v2 löst über `surface-has-plugins.v2` und
  `surface-plugin-protocols.v2` nach `plugin` auf. `MODE=enforce` bleibt bis zum bestandenen
  P6-Test gesperrt (siehe §7).

**Fixierte, ehrliche Garantie.** Auf OpenCode v1 gilt die Zusage `permission` —
**best-effort, nicht garantiert** (PARTIAL: keine Delegations-Provenienz, Child-Session-
Propagation unverifiziert). Auf OpenCode v2 löst die Oberfläche nach `plugin` auf, das Artefakt
läuft aber ausschließlich im Modus `observe` (nur Logging); die Durchsetzung trägt dort
weiterhin der `permissions[]`-Deny (`permission_deny_required`: Tier `plugin` **und** Modus
`observe`). Auf Providern ohne Hook gilt `advisory` (rein prompt-basiert). Nirgends wird eine
vollständig erzwungene Zusage behauptet; der einzige verifizierte Runtime-Gate bleibt der
`hook`-Tier.

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

Auf v2 schreibt dieselbe Gate-Ebene stattdessen `permissions[]`-Tripel
(`{action, resource: "**", effect: "deny"}`, ans Listenende); die PARTIAL-Grenze (keine
Delegations-Provenienz) gilt dort unverändert.

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

- `GATE_ENFORCED` = `true` für `hook` **und** `plugin` (so liefert es das Bundle). Auf Opencode
  v2 läuft das Plugin dennoch ausschließlich `observe`; die tragende Schicht ist der
  `permissions[]`-Deny.
- `GATE_PARTIAL` = `true` nur für `permission`.
- `GATE_ADVISORY` = `true` nur für `advisory`.

`rules/1-generic/use-orchestrator.md` rendert innerhalb `{{#if ORCH_MODE_STRICT}}`
genau einen der drei zueinander exklusiven Blöcke. Die `GATE_ENFORCED`-Variante
reproduziert den bisherigen Strict-Wortlaut **verbatim** (`# CRITICAL GATE` +
`… ALLES -> \`orchestrator\`. Keine Ausnahmen.`), sodass die Ausgabe
Hook-fähiger Provider byte-identisch bleibt (F-05). Opencode v2 rendert wegen des
aufgelösten Tiers `plugin` ebenfalls diesen Block; durchgesetzt wird die Zusage dort vom
`permissions[]`-Deny, nicht vom `observe`-Plugin. Die Provenienz trägt der
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
der Phase-1-Schema-Key (IC-16) und beeinflusst die Erzeugung des Artefakts nicht:
`runtime_gate._baked_plugin_mode()` liefert immer `observe`. P6 gated damit
ausschließlich `MODE=enforce`; für das Artefakt bleibt der Key deklarativ.

## 7. Phase-1-Grenze (P6) — `MODE=enforce` bleibt gesperrt

Die native OpenCode-Plugin-Tier ist für die v2-Surface **geliefert**, aber ausschließlich im
Modus `observe`:

- Der P6-Real-Repo-Test ist in dieser Umgebung nicht durchführbar. Ein unverifizierter
  „enforce"-Flip würde einen „erzwungen"-Anspruch ohne Nachweis ausliefern; das wird
  ausdrücklich **nicht** getan. P6 gated daher ausschließlich `MODE=enforce`.
- Das Plugin-Artefakt wird immer mit `MODE=observe` erzeugt
  (`runtime_gate._baked_plugin_mode()`); `permission_deny_required` hält deshalb die
  `permissions[]`-Tripel aktiv. Das Plugin ist additiv, nie Ersatz.
- `runtime_gate: plugin` bleibt in `config/provider-capabilities.yaml` uneingesetzt; die
  Tier `plugin` entsteht allein aus den aufgelösten Daten `surface-has-plugins.v2: true` und
  `surface-plugin-protocols.v2: opencode-plugin-v2-js`. Das statische `has_plugins: false`
  bleibt, damit v1 `permission` behält.
- Die v1-Artefakte (`templates/plugins/runtime-gate.opencode-plugin.js.tmpl`,
  `has_plugins: false`) bleiben unverändert; das v2-Template
  `templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl` ist observe-only und trägt
  keine enforce-Zusage.
- Es wird nie „vollständig erzwungen" behauptet; die fixierte Zusage ist auf OpenCode v1
  `permission` (best-effort, nicht garantiert), auf OpenCode v2 `plugin`+`observe` mit
  Permission-Deny und auf hook-losen Providern `advisory`.

**P6-Befunde (read-only Verifikation, belegen die observe-Grenze):**

- `tool.execute.before` kann nur per `throw` verweigern (kein anderer Blockier-Kanal).
- Das Hook-`input` trägt **keine Agent-Identität** (`{tool, sessionID, callID}`); die
  Bedingung „Main Chat im `input` unterscheidbar" (AN-5/OQ-2) ist damit **widerlegt**.
- AN-3/AN-4 (Child-Session-Propagation bzw. Feuern in Subagent-Sessions) sind nur
  ableitbar, **nicht bewiesen**; AN-6 (Root-Deny vs. Per-Agent-Frontmatter-Präzedenz)
  bleibt **ungeklärt**.

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
gekoppelt). Auf v2 läuft zusätzlich der tierunabhängige
`reconcile_opencode_surface_gate` (siehe §4).

## 9. Referenzen

- `scripts/lib/runtime_gate.py::RUNTIME_GATE_TIERS` — Tier-Vokabel (Seam).
- `scripts/lib/providers.py::provider_runtime_gate_tier` / `::runtime_gate_vars` — Resolver + Bundle.
- `config/provider-capabilities.yaml:capabilities.<provider>.runtime_gate` — deklarierte Tier.
- `scripts/lib/isolation.py::_sync_opencode_runtime_gate` — A2-Root-Deny/Merge.
- `scripts/lib/isolation.py::permission_deny_required` / `::reconcile_opencode_surface_gate` — v2-Gate-Ebene.
- `config/ai-providers.yaml:Opencode.surface-has-plugins` / `:surface-plugin-protocols` — Daten, die die Tier `plugin` für v2 auflösen.
- `templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl` — v2-Artefakt (observe-only).
- `scripts/lib/consistency/orchestrator_strict.py` — tier-abgeleitete Severity.
- `rules/1-generic/use-orchestrator.md`, `rules/1-generic/a2a-delegation-gates.md` — gestufte Zusage.
