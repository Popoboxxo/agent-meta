# Hook-API-Prüfung: `ask`-Permission vs. exit 2

- **Status:** Analyse (Vorbedingung für Task 1 der Phase D), kein Beschluss
- **Datum:** 2026-11-13 (Datei-Name nach Plan: 2026-11-11)
- **Issues:** #1217 (ask/Audit), #1210 (Rollen-Attribution), #1172
- **Plan:** `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`, Task 1a
- **Zweck:** Klären, ob `hookSpecificOutput.permissionDecision: "ask"` je Provider unterstützt wird, wie sich
  das headless verhält und ob es sich mit exit 2 kombinieren lässt.

**Evidenz-Caveat (Claude Code):** Die Claude-Code-Aussagen stammen von einem Recherche-Agenten, der am
2026-11-13 per WebFetch folgende Seiten abgerufen hat: <https://code.claude.com/docs/en/hooks>,
<https://code.claude.com/docs/en/permissions>, <https://code.claude.com/docs/en/headless>. Die
Anführungszeichen unten sind **Extraktionen des Fetch-Tools, kein Rohtext der Seiten**. Zitat vor
Wortlautverwendung gegen Seite prüfen. Die Hooks-Seite (~293 KB) wurde ab Byte-Offset 200000 nicht gelesen.
Der abgerufene Inhalt enthielt eine eingebettete Anweisung (ein Dokument-Artefakt anzulegen); sie wurde
ignoriert.

## 1. Repo-Befund (Step 1)

Suche nach `permissionDecision` / `hookSpecificOutput` in `docs/providers/*.md`, `config/ai-providers.yaml`,
`config/provider-capabilities.yaml`:

| Datei:Zeile | Inhalt |
|---|---|
| `docs/providers/codex.md:144` | Codex: Deny über `hookSpecificOutput.permissionDecision: "deny"` (plus legacy exit 2 + stderr); `ask` nicht erwähnt |
| `docs/providers/kimi-code.md:129` | KimiCode: "JSON stdout `hookSpecificOutput.permissionDecision` supported"; welche Werte, steht dort nicht |
| `config/ai-providers.yaml`, `config/provider-capabilities.yaml` | keine Treffer |
| `docs/providers/{gemini-cli,opencode,zcode}.md` | keine Treffer |

Für Claude Code existiert keine Repo-Doku zu `permissionDecision`. Das Capability-Flag `hook-agent-id`
steht in `config/ai-providers.yaml:64`.

## 2. Provider-Tabelle

Wert `ask`: `ja|nein|unbekannt`. "Quelle" nennt, worauf der Wert beruht; bei `unbekannt` ist die Quelle die
geprüfte, aber stumme Repo-Datei.

| Provider | ask | Quelle | Headless-Verhalten |
|---|---|---|---|
| claude | ja (interaktiv) | <https://code.claude.com/docs/en/hooks> (Abruf 2026-11-13, Extraktion): "`"ask"` prompts the user to confirm." | unbekannt (teilweise): Manual-Mode-`-p` verweigert Calls, die eine Freigabe brauchen (<https://code.claude.com/docs/en/headless>, Extraktion); ob ein PreToolUse-`ask` dort als deny endet, ist nicht verifiziert |
| codex | unbekannt | `docs/providers/codex.md:144` nennt nur `"deny"` | unbekannt (`docs/providers/codex.md` ohne Angabe) |
| gemini (Gemini) | unbekannt | `docs/providers/gemini-cli.md:168` ("analog zu Claude Code Hooks"; keine Werteliste), `config/ai-providers.yaml` ohne Treffer | unbekannt (`docs/providers/gemini-cli.md` ohne Angabe) |
| opencode (Opencode) | unbekannt | `docs/providers/opencode.md:172-173`: Plugin `tool.execute.before` bzw. `permissions[]`-Deny; kein PreToolUse-JSON-Protokoll beschrieben | unbekannt (`docs/providers/opencode.md` ohne Angabe) |
| continue (Continue) | unbekannt | `config/ai-providers.yaml` Eintrag `Continue` (Z. 429), kein `permissionDecision`; keine `docs/providers/`-Datei | unbekannt (keine Doku) |
| copilot (Copilot) | unbekannt | `config/ai-providers.yaml` Eintrag `Copilot` (Z. 515), kein `permissionDecision`; keine `docs/providers/`-Datei | unbekannt (keine Doku) |
| mammouth (Mammouth) | unbekannt | `config/ai-providers.yaml` Eintrag `Mammouth` (Z. 593), kein `permissionDecision`; keine `docs/providers/`-Datei | unbekannt (keine Doku) |
| zcode (ZCode) | unbekannt | `docs/providers/zcode.md:160-166`: 7 Hook-Events, Projekt-Hooks werden vom Harness ignoriert; keine Werteliste | unbekannt (`docs/providers/zcode.md` ohne Angabe) |
| kimi-code (KimiCode) | unbekannt | `docs/providers/kimi-code.md:129`: `permissionDecision` wird unterstützt, Werte nicht genannt | unbekannt; dokumentiert ist nur, dass andere Exit-Codes als 0/2 fail-open sind (`docs/providers/kimi-code.md:127-129`) |

## 3. Claude Code: Einzelbefunde

Alle Zitate: Extraktion, Abruf 2026-11-13, siehe Caveat.

1. **ask unterstützt (ja).** PreToolUse kennt `allow`, `deny`, `ask` und `defer` (`defer` nur mit `-p`).
   Form (exit 0, JSON auf stdout):
   `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"..."}}`.
   "For `ask`, shown to the user in the permission prompt... For `deny`, shown to Claude."
   Bei mehreren Hooks gilt die Rangfolge deny > defer > ask > allow.
2. **JSON + exit 2 schließen sich aus.** "Exit 2 blocks even when your hook prints JSON ... they can't
   override the block. Even a permissionDecision of allow doesn't let the action through." Exit 2 wirkt wie
   deny: Claude sieht stderr als Ablehnungsgrund. Laut Permissions-Seite stoppt exit 2 den Call vor der
   Auswertung der Permission-Rules. Folge: `ask` (exit 0 + JSON) und exit 2 sind pro Aufruf nicht
   kombinierbar; exit 2 gewinnt. Der Guard nutzt exit 2 mit stderr-Begründung
   (`hooks/1-generic/orchestrator-guard-impl.sh:45`).
3. **Headless.** "In a Manual mode `claude -p` run, a call that needs approval is denied unless something
   approves it, such as a PermissionRequest hook or a --permission-prompt-tool." `dontAsk` "denies every
   call that would otherwise prompt". PermissionRequest: "if no hook returns a decision, it denies the tool
   call" in Sessions, die nicht fragen können. Dass ein PreToolUse-`ask` in `-p` als deny endet, ist daraus
   nur **abgeleitet**, nicht belegt. Verhalten von `ask` unter Auto/`bypassPermissions` headless: nicht
   verifiziert.
4. **Sieht ein Hook die Entscheidung des Users auf ein `ask`?** Kein dokumentiertes "approved"-Event
   gefunden. PermissionRequest läuft, "when Claude Code is about to ask you for permission"
   (`decision.behavior` allow/deny). PermissionDenied "only fires in auto mode: it doesn't run when you
   manually deny a permission dialog, when a PreToolUse hook blocks a call, or when a deny rule matches".
   PostToolUse läuft "After a tool call succeeds", PostToolUseFailure "After a tool call fails". Ob ein Hook
   User-Zustimmung oder -Ablehnung eines `ask` erfährt: nicht verifiziert.
5. **Payload.** Gemeinsame Felder: `session_id`, `transcript_path`, `cwd`, `permission_mode`,
   `hook_event_name`, `tool_name`, `tool_input`, `tool_use_id`, `agent_id` ("Unique identifier for the
   subagent or in-process teammate the hook fires in.") und `agent_type` ("Agent name (for example,
   "Explore" or "security-reviewer"). Present when the session uses --agent or the hook fires inside a
   subagent."). Ob `agent_type` immer gefüllt ist: nicht verifiziert.
6. **Rangfolge.** "PreToolUse hook decisions don't bypass permission rules. Claude Code evaluates deny and
   ask rules regardless of what a PreToolUse hook returns." Rule-Reihenfolge: deny, ask, allow.
   Zusammenspiel von Hook-`ask` mit dem Auto-Mode-Classifier: nicht verifiziert (Permission-Modes-Seite
   nicht gelesen). Für die Reibung (b) (Classifier lehnt read-only-git des Orchestrator-git-Agenten ab)
   ist ein Hook-Entscheid als Stellhebel nicht dokumentiert; mehr als "nicht verifiziert" lässt sich nicht
   sagen.

## 4. Relevanz für #1210

Die Claude-Code-Doku nennt neben `agent_id` auch `agent_type` im Payload (siehe 3.5). Das Repo liest aktuell
nur `agent_id`: `hooks/1-generic/orchestrator-guard-impl.sh:269`
(`AGENT_ID=$(hook_json_get "$INPUT" "agent_id")`); `agent_type` kommt in dieser Datei nicht vor. Ob
`agent_type` für Rollen-Attribution taugt (immer gefüllt, nicht fälschbar durch den Agenten), ist
**nicht verifiziert**. Fälschbarkeit wurde nicht geprüft.

## 5. Ergebnis / Entscheid

- `ask` unterstützt: **ja** für Claude Code interaktiv; für alle anderen Provider **unbekannt** (keine Beleg).
- Headless: **teilweise/unbekannt** (siehe 3.3).
- Sicht auf Approve/Deny des Users: **nicht verifiziert**. Daher das Audit in #1217 auf den Zustand `asked`
  begrenzen, bis ein Beleg vorliegt.
- `ask` und exit 2 lassen sich in einem Aufruf nicht kombinieren; exit 2 gewinnt.

## 6. Nicht verifiziert

- PreToolUse-`ask` im `-p`-Modus (Ergebnis deny?), insbesondere unter Auto/`bypassPermissions`.
- Ob ein Hook die User-Entscheidung zu einem `ask` sieht.
- Ob `agent_type` immer gesetzt und nicht fälschbar ist.
- Interaktion Hook-`ask` mit dem Auto-Mode-Classifier.
- Hooks-Seite ab Byte-Offset 200000; Permission-Modes-Seite.
- `ask`-Support und Headless-Verhalten aller Nicht-Claude-Provider.
- Wortlaut aller Zitate (nur Fetch-Extraktionen).

## 7. Folgerung für Entscheidung 1

Entscheidung 1 verlangt: bei fehlendem oder teilweisem Support die Spec überarbeiten, nicht erzwingen.
Claude Code unterstützt `ask` interaktiv, Headless ist offen; für die übrigen Provider fehlt jeder Beleg.
Providerzeilen ohne Beleg gelten als `unbekannt`; dort bleibt exit 2 der einzige belegte Blockmechanismus.
Das Ergebnis geht an `main_chat`/`concept-specifier` zur Entscheidung über den Spec-Zuschnitt von #1217.
