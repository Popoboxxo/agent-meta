---
status: geplant
date: 2026-11-23
spec-id: SPEC-DECISION-1329-SHELL-GRANT
spec-status: APPROVED
contract-spec-id: SPEC-OPENCODE-WORKER-SHELL-TOOL-1329
contract-spec-status: APPROVED
branch: fix/decision-points-bundle-20261123
base-head: 52bb8d9
pipeline_stages:
  implement: 1
  review-req: 5
  review-quality: 6
  validate: 7
---

# Decision #1329 — Opencode-Worker Shell-Grant Implementation Plan

> Status: geplant. Source-Spec `status: APPROVED` (User, 2026-11-23, Einzelentscheidung),
> Contract-Spec `status: APPROVED` (User, 2026-11-23, generelle Freigabe). Bindende Entscheidung =
> **Option (a) grant**: Opencode-Subagent-Worker erhalten das Shell-Tool, wenn `bash: allow`
> konfiguriert ist. (b)/(c) sind verworfen und werden nicht re-geöffnet.
> Diese Datei wurde von der Planungsrolle erstellt — keine Implementierung, kein Commit, kein
> Push/Tag/Merge. Branch `fix/decision-points-bundle-20261123` @ `52bb8d9`.

**Goal:** Die deklarierte Shell-Capability generierter Opencode-Worker mit der tatsächlich
verfügbaren Capability in Deckung bringen (v1 `permission.bash`, v2 `permissions[shell]`), sodass
Execution-Rollen nur mit gemessenem Prozess-Exit-Code Erfolg behaupten. Keine erfundenen
Verify-Evidence mehr (Live-Fall `test-executor`: „20/20 pytest grün" ohne Lauf).

**Architecture:** `config/provider-capabilities.yaml` → `capabilities.<Provider>.subagent-shell`
(+ `subagent-shell-verified-state`) → `_apply_agent_transform` / `_caps` → v1/v2-Mapper in
`provider_transform.py` → `agent_sync.py`-Renderpfad → deterministischer Post-Render-Gate in `tests/`
→ generierte Artefakte. Reuse des `#1113`-Capability-Mechanismus, kein neues ad-hoc Flag-Source.

**Tech Stack:** Python 3.9, Stdlib + PyYAML, Markdown-Templates mit `{{...}}`-Platzhaltern,
pytest, `python3 scripts/sync.py`; provider-agnostisch (Capability-Keys/Config-Flags, nie
`if provider == "Name"` — `provider-agnostic`-Skill).

**Spec:** docs/specs/2026-11-23-decision-1329-shell-grant-spec.md (APPROVED, `SPEC-DECISION-1329-SHELL-GRANT`)
**Contract-Spec:** docs/specs/2026-11-23-opencode-worker-shell-tool-1329-spec.md (APPROVED, `SPEC-OPENCODE-WORKER-SHELL-TOOL-1329`)
**Estimated effort:** `effort-estimator` (Textverweis; keine eigene Aufwandszahl — Schätzung
erfolgt durch die genannte Rolle).

## Global Constraints

- Nur diese eine Plan-Datei wird von der Planungsrolle geschrieben. Kein Code, kein Commit, kein Push/Tag/Merge, kein Worktree-Isolation.
- Bindend ist (a) grant. Kein Re-Open von (b)/(c), keine neue Produktentscheidung, keine Spec-Änderung.
- Provider-agnostisch: keine Provider-Literal-Verzweigung in geänderten Pfaden; alle Effekte über Capability-Keys/Config-Flags (`tests/test_provider_agnostic_dispatch.py` muss grün bleiben).
- Claude/Gemini-Renderoutput bleibt byte-identisch zu `278ba54f`; keine Permission-Posture-Änderung, kein Bruch des Orchestrator-Write-Locks (`_WRITE_SCOPE_LOCKED_ROLES`).
- Fail-safe: fehlender/`false`/ungültiger `subagent-shell`-Key **oder** `subagent-shell-verified-state != VERIFIED-RUNTIME` **oder** Rolle ohne `bash: allow` ⇒ `deny`/fehlt + WARNING. Nie `allow`.
- **Review minor (verbindlich in AC-1/AC-2):** `subagent-shell: true` ist nur wirksam bei `subagent-shell-verified-state: VERIFIED-RUNTIME`. Verhindert, dass der Gate eine Papier-Deklaration gegen einen nicht liefernden Harness freigibt.
- Keine erfundene Evidence: Shell-Ausführung und Test-Erfolg nur mit gemessenem Exit-Code behaupten. Keine LLM-Runs, keine echten Test-Suite-Läufe in diesem Schritt.
- Post-Render-Gate ist finding-basiert und fail-soft — kein `sys.exit` im Gate-Layer (Muster `scripts/lib/consistency/subagent_permissions.py:18-19`).
- Reuse des bestehenden Mechanismus (`supports-permission-deny`, #1113); `config/ai-providers.yaml` `tools-format: keep` bleibt, kein neues ad-hoc Flag.
- Mammouth-Fork erbt das Muster, ist aber bewusst out of scope.
- Python 3.9, keine neuen Dependencies. Conventional Commits (Englisch, Imperativ, ≤72 Zeichen, ohne BOM), Trailer gemäß Projekt-Config, **keine Closing-Keywords** (`Fixes`/`Closes`/`Resolves #1329`) — Referenz nur als `(#1329)`.
- Shell-Kommandos mit `rtk`-Präfix. Testkommando: `python3 -m pytest <pfad> -q`; Abschluss: `python3 scripts/sync.py --validate` Exit 0.

## File Structure

- Modify: `config/provider-capabilities.yaml` (`:189-247`) — `subagent-shell` + `subagent-shell-verified-state` (+ optional `subagent-shell-reason`) für alle Provider explizit; Opencode `true`/`VERIFIED-RUNTIME`, übrige `false`/`UNVERIFIED` (rein deklarativ). Task 1.
- Modify: `scripts/lib/provider_transform.py` (Mapper `:889-937`, `:954-989`; Signaturen `:991-1149`, `:1262ff.`; Aufrufer `:611-622`; `_caps` `:447`) — Shell-Effekt an Capability + verified-state koppeln. Task 1.
- Modify: `scripts/lib/agent_sync.py` (`:149-201` render_bash/Commit-Grant, `:1348` Transform-Aufruf, `:1858`) — Bash-Injektion für Shell-Rollen bleibt wirksam, kein Subagent-Sonderpfad. Task 1.
- Modify (nur Kommentar/Verweis, keine funktionale Änderung): `config/ai-providers.yaml` (`:378-395`) — Reuse des `agent-transform`-Mechanismus. Task 1.
- Create: `tests/test_opencode_worker_shell_grant.py` — v1/v2-Mapper-Parameterisierung, Fail-safe-Fälle, Verified-State-Bedingung. Task 1.
- Create: `tests/test_opencode_worker_shell_gate.py` — deterministischer Post-Render-Gate, Finding mit Rolle+Datei+Mode, kein `sys.exit`. Task 2.
- Modify: `agents/1-generic/{test-executor,code-reviewer,e2e-tester,git,developer,devops-engineer,tester}.md` — Evidence-Regel: Erfolg nur mit gemessenem Exit-Code. Task 3.
- Create: `tests/test_execution_role_evidence_discipline.py` — pinnt die Exit-Code-Regel in allen sieben Templates. Task 3.
- Modify: `docs/providers/multi-provider.md` — Shell-Verfügbarkeit pro Provider/Mode + Fallback + fehlender Primary-Mode-Key. Task 4.
- Create: `tests/test_shell_capability_docs.py` — pinnt die Doku-Invariante ohne Code-Branch-Abhängigkeit. Task 4.
- Keine Änderung: `agents/1-generic/orchestrator.md` (`bash: deny`, Router-Posture), `.meta-config/project.yaml`, `.gitmodules`.

---

## Tasks

### Task 1: Capability-Keys und v1/v2-Mapper koppeln (AC-1, AC-2)

**Agent / Tier:** `developer` · **Depends on:** — · **Stage:** implement (Schritt 1)

**Files:** Modify `config/provider-capabilities.yaml`, `scripts/lib/provider_transform.py`,
`scripts/lib/agent_sync.py`, `config/ai-providers.yaml` (Kommentar) · Test: Create
`tests/test_opencode_worker_shell_grant.py`.

**Interfaces:**
- Consumes: Template-`tools: [.., Bash]` (z. B. `agents/1-generic/test-executor.md:9-12`), `provider_capabilities`-Dict (`provider_transform.py:447`).
- Produces: `capabilities.Opencode.subagent-shell` + `...verified-state`; erweiterte Mapper-Signaturen `subagent_shell: bool`, `subagent_shell_verified_state: str`.

**Akzeptanzkriterien (aus Spec, mit Review minor):**
- AC-1 (Grant): Given `subagent-shell: true` **und** `subagent-shell-verified-state: VERIFIED-RUNTIME` und eine Rolle mit `bash: allow`; When als Opencode-`subagent` gerendert (v1 und v2); Then v1 `permission.bash: allow`, v2 `permissions[shell].effect: allow`.
- AC-2 (Fail-safe): Given Key fehlt/`false`/ungültig **oder** verified-state `!= VERIFIED-RUNTIME` **oder** Rolle ohne `bash: allow`; When gerendert; Then `bash`/`shell` `deny` oder fehlt, nie `allow`, WARNING/Finding liegt vor.
- Contract-Spec AC-1/AC-2 (Capability-Parität, deny-Kopplung).

**Task-level clarification (keine Produktentscheidung):**
- Exakter Key-Name `subagent-shell` / `subagent-shell-verified-state` folgt dem Contract-Spec; Vorgabe eines anderen Keys durch den Owner = Implementierungsdetail, kein Re-Open von (a).
- „`bash: allow` konkretisiert" = generierte Rollen-Permission aus Template-`Bash`, nicht `opencode.jsonc` `permission.bash: {}`; bei abweichender Lesart kurz bestätigen.
- `subagent-shell: true` setzen nur mit `verified-state: VERIFIED-RUNTIME` (Review minor).

- [ ] Step 1 (rot): Tests schreiben — parametrisiert v1 `_map_claude_tools_to_opencode_permissions` / v2 `map_tools_to_opencode_v2_permissions` mit `(grant=true+VERIFIED-RUNTIME → allow)`, `(false|fehlt|ungültig → deny + WARNING)`, `(verified-state != VERIFIED-RUNTIME → deny)`, `(Rolle ohne Bash → deny)`, `(deny_list-Parität v1)`. Fehlt der Parameter, schlägt der Import/ die Assertion fehl.
- [ ] Step 2 (grün): Capability-Block ergänzen (Opencode `true`/`VERIFIED-RUNTIME`, übrige `false`/`UNVERIFIED`); `_caps`-Auflösung aus `:447` an beide Mapper und an `_transform_frontmatter_for_opencode`/`_v2` durchreichen (`:611-622`); Mapper-Signaturen um die zwei Parameter erweitern; `agent_sync.py` Bash-Injektion unverändert lassen; `ai-providers.yaml` nur Verweis-Kommentar.
- [ ] Step 3 (pass): `python3 -m pytest tests/test_opencode_worker_shell_grant.py -q` grün; `python3 scripts/sync.py --validate` Exit 0; `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` grün.
- [ ] Step 4 (commit): `feat: grant opencode worker shell via capability flag` + Trailer gemäß Config; Referenz `(#1329)`, kein Closing-Keyword.

### Task 2: Deterministischer Post-Render-Gate (AC-4)

**Agent / Tier:** `developer` · **Depends on:** 1 · **Stage:** implement (Schritt 2)
*(file-disjunkt zu Task 3/4 — nach 1 parallel ausführbar)*

**Files:** Create `tests/test_opencode_worker_shell_gate.py`. Keine Produktionsdatei.

**Interfaces:**
- Consumes: gerenderte Artefakte aus Task 1 + `subagent-shell`/verified-state aus `provider-capabilities.yaml`.
- Produces: `gate_check(...) -> dict` mit `finding{role, file, mode}`, fail-soft, kein `sys.exit`.

**Akzeptanzkriterien:**
- AC-4: Given manipuliertes Artefakt mit `bash: allow` bei `subagent-shell: false`; When der Gate läuft; Then finding mit Rolle + Datei + Mode, kein Still-Pass.
- Zusätzlich: Deklaration ≡ Rendering für alle gerenderten Rollen (v1+v2); Contract-Spec AC-3.

- [ ] Step 1 (rot): Zwei Tests — `test_divergent_render_is_reported` (Fixtures: `bash: allow` @ `false` → Finding mit role/file/mode) und `test_all_roles_declared_equals_rendered`. Vor Implementierung fehlt `gate_check` ⇒ Fail.
- [ ] Step 2 (grün): `gate_check` im Testmodul implementieren — liest Capability + gerendertes Frontmatter, vergleicht pro Rolle/Mode, liefert Finding-Dict; bei ungültigem Key `deny` + WARNING; niemals `sys.exit`.
- [ ] Step 3 (pass): `python3 -m pytest tests/test_opencode_worker_shell_gate.py -q` grün (Divergenz-Fall rot bei manipulierter Fixture, grün bei korrekter); `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4 (commit): `test: add post-render shell declaration gate` + Trailer; Referenz `(#1329)`, kein Closing-Keyword.

### Task 3: Evidence-Disziplin in Execution-Rollen (AC-3)

**Agent / Tier:** `developer` · **Depends on:** 1 · **Stage:** implement (Schritt 3)
*(file-disjunkt zu Task 2/4)*

**Files:** Modify `agents/1-generic/{test-executor,code-reviewer,e2e-tester,git,developer,devops-engineer,tester}.md` · Test: Create `tests/test_execution_role_evidence_discipline.py`.

**Interfaces:**
- Consumes: bestehende Output-Contracts/`<constraints>` der sieben Templates; `EXIT_CODE`-Feld (`test-executor.md:100`).
- Produces: eine kanonische, provider-neutrale Regel pro Template: Erfolgsbehauptung nur mit gemessenem Exit-Code.

**Akzeptanzkriterien:**
- AC-3: Given Execution-Rolle ohne gemessenen Prozess-Exit-Code; When sie antwortet; Then keine Erfolgsbehauptung („tests passed", „20/20 grün") — Regel im Prompt nachweisbar. Contract-Spec AC-4.

- [ ] Step 1 (rot): Test pinnt pro Template das Vorhandensein der Exit-Code-Regel + Abwesenheit von Erfolgsbehauptungen ohne `EXIT_CODE`; vor Edit fehlgeschlagen.
- [ ] Step 2 (grün): Einheitlichen Satz in `<constraints>`/Output-Contract der sieben Templates ergänzen; `tools`/Bash-Posture unverändert; kein Provider-Name, keine Capability-Logik in Prosa.
- [ ] Step 3 (pass): `python3 -m pytest tests/test_execution_role_evidence_discipline.py -q` grün; `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4 (commit): `docs: bind execution-role success claims to exit codes` + Trailer; Referenz `(#1329)`, kein Closing-Keyword.

### Task 4: Capability-Matrix-Doku (Contract AC-5)

**Agent / Tier:** `technical-writer` · **Depends on:** 1 · **Stage:** implement (Schritt 4)
*(file-disjunkt zu Task 2/3)*

**Files:** Modify `docs/providers/multi-provider.md` · Test: Create `tests/test_shell_capability_docs.py`.

**Interfaces:**
- Consumes: `subagent-shell`, `subagent-shell-verified-state` aus Task 1.
- Produces: dokumentierte Shell-Verfügbarkeit je Provider × Modus (primary/subagent), Fallback `deny` + WARNING, expliziter Fall ohne Primary-Mode-Key.

**Akzeptanzkriterien:**
- Contract AC-5: Given Capability-Matrix-Doku; When ein Consumer sie liest; Then Shell-Verfügbarkeit pro Provider/Mode + Fallback dokumentiert — ohne Code-Branch-Abhängigkeit. Fehlt `primary-role`/`mode`, greift der bestehende Fail-safe `mode: subagent` (`provider_transform.py:1069`); Shell dann nach `subagent-shell` beurteilt, bei `false`/UNVERIFIED ⇒ `deny`. Keine neue Primary-Posture erfunden.

- [ ] Step 1 (rot): Test erwartet die dokumentierten Begriffe (`subagent-shell`, `VERIFIED-RUNTIME`, `deny`, `WARNING`, `primary`, `subagent`, Default-`subagent`) — vor Edit Fail.
- [ ] Step 2 (grün): Abschnitt in `multi-provider.md` ergänzen; Aussagen rein deklarativ, kein `if provider == ...` in der Doku-Logik.
- [ ] Step 3 (pass): `python3 -m pytest tests/test_shell_capability_docs.py -q` grün.
- [ ] Step 4 (commit): `docs: document opencode subagent shell capability` + Trailer; Referenz `(#1329)`, kein Closing-Keyword.

### Task 5: Review Stufe 1 — Requirements (`review-req`)

**Agent / Tier:** `validator` · **Depends on:** 2, 3, 4 · **Stage:** review-req (Schritt 5)
**Files:** keine (reine Prüfung). **Interfaces:** Consumes Tasks 1–4; Produces Pass/Fail je AC.

- [ ] Step 1: AC-1…AC-5 (Entscheidungs-Spec) + AC-1…AC-5 (Contract-Spec) gegen Diff und Tests abgleichen; Verified-State-Bedingung in AC-1/2 prüfen; keine neuen Entscheidungen/Dateien, kein Closing-Keyword, Claude/Gemini-Byte-Identität bestätigt.
- [ ] Step 2: Bei Rot → Befund an verantwortlichen Task zurück, kein Merge. Kein Commit.

### Task 6: Review Stufe 2 — Quality (`review-quality`)

**Agent / Tier:** `code-reviewer` · **Depends on:** 5 · **Stage:** review-quality (Schritt 6)
**Files:** keine. **Interfaces:** Consumes Tasks 1–4 + Review 5; Produces Blast-Radius/SOLID/DRY-Bericht.

- [ ] Step 1: Blast-Radius, SOLID/DRY, keine Provider-Literale (AST-Scan `test_provider_agnostic_dispatch.py`), `deny_list`-Parität, Gate fail-soft ohne `sys.exit`, keine erfundene Evidence.
- [ ] Step 2: Bei Rot → zurück an Task; bei Grün → Final-Validation freigeben. Kein Commit.

### Task 7: Final-Validation (`validate`)

**Agent / Tier:** `tester` · **Depends on:** 6 · **Stage:** validate (Schritt 7)
**Files:** keine (Ausführung bestehender Tests). **Interfaces:** Consumes alle Tasks; Produces Testprotokoll + AC-Abdeckungsnachweis.

- [ ] Step 1: `python3 -m pytest tests/test_opencode_worker_shell_grant.py tests/test_opencode_worker_shell_gate.py tests/test_execution_role_evidence_discipline.py tests/test_shell_capability_docs.py tests/test_provider_agnostic_dispatch.py -q` → 0 failed.
- [ ] Step 2: `python3 scripts/sync.py --validate` Exit 0; generierte Claude/Gemini-Artefakte byte-identisch zu `278ba54f` (read-only gegen Baseline, AC-5).
- [ ] Step 3: Bestätigen, dass keine echten Shell-/Test-Suite-Läufe als Behauptung auftreten; Protokoll an Orchestrator. Kein Commit, kein Push/Tag/Merge.

---

## AC Coverage Map

| AC | Quelle | Task(s) | Messbares Artefakt |
|---|---|---|---|
| AC-1 Grant (+ Verified-State) | Entscheidungs-Spec | 1, 5, 7 | v1 `permission.bash: allow`, v2 `permissions[shell].effect: allow` |
| AC-2 Fail-safe (+ Verified-State) | Entscheidungs-Spec | 1, 2, 5, 7 | `deny`/fehlt + WARNING für alle Fail-Fälle |
| AC-3 Keine erfundene Evidence | Entscheidungs-Spec | 3, 5, 7 | Exit-Code-Regel in 7 Templates, Test pinnt sie |
| AC-4 Post-Render-Gate | Entscheidungs-Spec | 2, 5, 7 | Finding.role/file/mode bei manipuliertem Artefakt |
| AC-5 Posture-Schutz | Entscheidungs-Spec | 1, 5, 6, 7 | Claude/Gemini byte-identisch zu `278ba54f` |
| Contract AC-1/2 Deklaration≡Verfügbarkeit | Contract-Spec | 1, 5 | Mapper-Parametrisierung grün |
| Contract AC-3 Post-Render-Gate | Contract-Spec | 2, 7 | Gate-Finding grün/rot wie spezifiziert |
| Contract AC-4 Evidence-Discipline | Contract-Spec | 3, 7 | Output-Contract-Regel nachweisbar |
| Contract AC-5 Dokumentation | Contract-Spec | 4, 5, 7 | Doku-Test grün, kein Code-Branch |

Jede AC mappt auf mindestens einen Interface-Contract; keine AC ohne Test.

## Re-planning

Nach jedem Task-Boundary (besonders nach Task 1 Mapper-Kopplung, nach den Reviews 5/6 und vor
Task 7) Annahmen neu prüfen: Trägt `subagent-shell-verified-state` noch `VERIFIED-RUNTIME`? Ist die
`bash: allow`-Auslegung (Template-Bash, nicht `opencode.jsonc`) noch konsistent? Sind die ACs noch
abgedeckt? Plan aktualisieren statt einfrieren.

## Self-Review

- Jeder Task mappt auf genau eine vorhandene Rolle: 1–3 `developer`, 4 `technical-writer`, 5 `validator`, 6 `code-reviewer`, 7 `tester`. Jedes AC ist messbar (Dateiinhalt, Exit-Code, Finding-Felder, Byte-Vergleich).
- `Files:`/`Interfaces:` vollständig; Tasks 2/3/4 sind file-disjunkt und hängen nur an 1; Reviews 5–7 haben keine Files. Keine Dateiüberlappung innerhalb einer Gruppe.
- `pipeline_stages` deckt alle vier `plan-driven`-Stages ab: `implement: 1`, `review-req: 5`, `review-quality: 6`, `validate: 7` — kein Fallback-Agent.
- Keine Platzhalter, keine `TBD`, keine erfundenen Testbefunde; Anker gegen Branch-Head `52bb8d9` gemessen; Spec + Contract-Spec referenziert.
- Provider-agnostisch (kein `if provider == ...`), keine Closing-Keywords, kein BOM, kein Push/Tag/Merge durch die Planungsrolle.
- Effort: `effort-estimator` als Textverweis, keine eigene Aufwandszahl.
