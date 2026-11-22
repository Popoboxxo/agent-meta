# Antigravity runtime probe runbook (#860)

Status: **RUNBOOK ONLY — the external probe is out of scope for G-PR1.**
This document describes *how* to run the Antigravity (`agy`) runtime probe; it
does not implement Antigravity support and does not record a probe result.

Scope notes:

- Issue **#860** is externally blocked: on the audit host `agy` aborts with
  `SIGILL` / **Exit 132** because the binary requires the `pclmul` CPU feature.
  Owner comments (2026-10-27 / 2026-10-29) confirm the block. Executing the
  probe (plan Task 5) belongs to **G-PR2**, not to this change.
- Per **E-26**, Gemini support is CLI-only; there is no Antigravity variant in
  agent-meta. This runbook supports *diagnosis* of the external runtime, not
  the addition of an Antigravity target.
- Each real agent/provider invocation during the probe is gated by a cost
  estimate and an explicit user "yes" (decision G-O3, still open). Without that
  approval, run only the local/static checks below.

## 1. Prerequisites (the gate)

The probe may only proceed when **one** of the following holds:

1. A `pclmul`-capable host where `agy --help` exits 0, **or**
2. A genuine AGY IDE session in which the runtime is available.

### 1.1 Check the CPU feature

```bash
grep -c pclmul /proc/cpuinfo
```

- Result `>= 1` → the host has the required feature; continue to §1.2.
- Result `0` → the host cannot run the current `agy` binary. Stop here: the
  runtime layer is **UNVERIFIABLE** on this machine. Do not attempt a fake fix
  (`GODEBUG=cpu.pclmul=off`, `cpu.all=off`) — the failure comes from a
  GOAMD64=v3 code path in the binary, not from a generator defect.

### 1.2 Check the binary

```bash
agy --help
```

- Exit code `0` → prerequisite met; continue to §3.
- **Exit 132** (`SIGILL`, message: *"This binary was compiled with pclmul
  enabled, but this feature is not available on this processor
  (go/sigill-fail-fast)"*) → the same blocker as on the audit host. Record it
  as evidence (see §5) and stop; issue #860 stays open.

If the prerequisite is not met, Task 5 remains open and **no evidence commit
is created**. The runbook itself (this file) is complete and executable
regardless of the host.

## 2. Verdicts to confirm

The probe targets the verdicts below. They were derived from the in-binary
STATIC contract because the runtime layer was previously UNVERIFIABLE
(`agy --help` SIGILL / no `pclmul`). Reference docs:
`docs/analysis/2026-09-30-provider-audit-docs-part1.md` (§2, G-verdicts,
cross-provider summary), `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md`
(H2/H3 tally), and evidence
`docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` (§2).

| Verdict | Area | What the runtime probe must confirm |
|---|---|---|
| **G-1** | Agent discovery | Generated agents are read from `.agents/agents/<name>.md` (not `.gemini/agents/`); the actual discovery directory on a live AGY workspace. |
| **G-2** | Tool vocabulary | `tools:` names (e.g. `run_command`, `view_file`) are accepted; an unmapped name must not hang the subagent. |
| **G-3** | Model tier | `model:` values resolve on a live invocation (`inherit` / `flash` / `pro`); the concrete model IDs used by generated agents are accepted. |
| **G-7** | MCP servers | Workspace MCP config is `.agents/mcp_config.json` and uses `serverUrl`; legacy `url` / `httpUrl` in `.gemini/settings.json` are rejected. |
| **H2** | Hook command base | Hook handler command resolves with working directory = directory containing `hooks.json` (i.e. `<repo>/.agents/`), so `./hooks/antigravity-json-adapter.sh` exists. Related: **#1032** (hook cwd semantics; pinned as STATIC documentation, runtime confirmation still open). |
| **H3** | Hook matcher | `"matcher": "*"` is accepted and matches all tools on both `PreToolUse` groups. |

G-1/G-2/G-3/G-7 are HIGH deviations from the Antigravity contract; H2 and H3
are currently REFUTED/VERIFIED `[STATIC]` only and lack the runtime layer.

## 3. Probe steps

For each verdict, run the listed check on a host/session that passed §1.
Capture the exact command and output for the evidence template (§5).

1. **H2 / #1032 — hook command resolution.**
   ```bash
   ls -l .agents/hooks/antigravity-json-adapter.sh
   ls -l .agents/hooks/orchestrator-guard.sh
   ```
   Trigger a `PreToolUse` hook in a real AGY session and confirm the handler
   runs from `<repo>/.agents/` and both paths resolve. Compare with the
   documented cwd rule and with the #1032 pin.

2. **H3 — matcher wildcard.** Confirm a `"matcher": "*"` `PreToolUse` group
   fires for multiple distinct tool names in the live session.

3. **G-1 — discovery.** From a real AGY workspace, confirm generated agents
   appear as subagents and that the source directory is `.agents/agents/`.
   Note whether `.gemini/agents/` is ignored.

4. **G-2 — tool vocabulary.** Invoke a generated agent with its configured
   `tools:` list; confirm no hang and no "unmapped tool" failure for the
   mapped names from plan Task 4 / audit part1 §2.

5. **G-3 — model tier.** Invoke a generated agent and confirm the configured
   `model:` tier/model resolves. Record the effective model from the session
   output (secrets redacted).

6. **G-7 — MCP config.** Confirm `.agents/mcp_config.json` with `serverUrl`
   is loaded and that a legacy `url`-only entry in `.gemini/settings.json` is
   rejected as documented.

Any step that requires a live provider call needs the G-O3 cost estimate and
explicit user approval first; otherwise mark it `not run — no cost approval`.

## 4. Secrets redaction

Before recording any output, redact tokens, API keys, session IDs and user
data (replace with `<redacted>`). Capture structure and error text, not
credentials.

## 5. Evidence template

Copy this block into `docs/analysis/evidence/<date>-runtime-antigravity-pclmul.md`
(plan Task 5) once the prerequisite is met:

```markdown
# Antigravity runtime probe evidence (<date>)

- Host: <hostname / OS / agy version>
- CPU flags: <output of: grep -c pclmul /proc/cpuinfo>  (pclmul: yes/no)
- Prerequisite: agy --help exit <code>  (0 = pass, 132 = SIGILL/blocker)
- Session: <local CLI | real AGY IDE session>

| Verdict | Command | Output (secrets redacted) | Verdict after probe |
|---|---|---|---|
| H2 / #1032 | <command> | <output> | <REFUTED/VERIFIED/UNVERIFIABLE> |
| H3 | <command> | <output> | <...> |
| G-1 | <command> | <output> | <...> |
| G-2 | <command> | <output> | <...> |
| G-3 | <command> | <output> | <...> |
| G-7 | <command> | <output> | <...> |

Notes: <deviations from STATIC contract, cost approvals, open questions>
```

## 6. Outcome handling

- **Prerequisite unmet (Exit 132 / no pclmul):** record the blocker, leave
  #860 open, no evidence commit. Runtime verdicts stay UNVERIFIABLE `[STATIC]`.
- **Prerequisite met and probe run:** write the evidence file, update the
  verdicts in `docs/analysis/2026-09-30-provider-audit-docs-part1.md`, and
  (with approval) release the G-PR2 block for Task 0c / #1032. This is a
  separate task (Task 5) and is not part of the runbook deliverable.
