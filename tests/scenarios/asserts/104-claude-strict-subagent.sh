#!/bin/bash
# Scenario assert for 104-claude-strict-subagent.
# (issue #1190, SPEC-orchestrator-mode-topology-2026-11-09 §3.8.3/§12.4,
#  AC-29.)
#
# Position POS-2 on Claude — `mode: strict` + declared `topology: subagent`.
# Claude has no `mode: primary` concept and no entry-point surface at all, so
# the position is enforced by the `hook` tier: the strict gate text must be
# present in the rendered `use-orchestrator` rule, and nothing may point at an
# orchestrator session entry.
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# `--validate` (rc 0).
#
# Parts:
#   1. The fixture really declares the POS-2 pair for Claude (fixture drift).
#   2. The orchestrator role IS emitted (POS-2 = delegated orchestrator) and the
#      rule describing the gate is rendered.
#   3. `hook`-tier gate text: exactly one `# CRITICAL GATE` variant, the ENFORCED
#      one (no `(advisory)` / `(neutral)` / `(runtime-partially enforced)`
#      heading) and the enforced strict sentence in it.
#   4. No orchestrator entry point: `default_agent` appears in no settings /
#      opencode document (AC-29 "kein Entry-Point auf den Orchestrator").
#   5. No unresolved `{{PLACEHOLDER}}` in the generated agents and rules.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (104-claude-strict-subagent): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (104-claude-strict-subagent): $*"
    exit 1
}

AGENT=".claude/agents/orchestrator.md"
RULE=".claude/rules/use-orchestrator.md"
[ -f "$AGENT" ] || fail "POS-2 emits the role: $AGENT must exist"
[ -f "$RULE" ] || fail "missing rendered gate rule: $RULE"

# --- 1. Fixture = POS-2 (strict x subagent) for Claude. ---------------------
python3 - .meta-config/project.yaml <<'PY' || fail "fixture is not the Claude POS-2 (strict x subagent) project"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
assert [p for p in (project.get("ai-providers") or [])] == ["Claude"], project.get("ai-providers")
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "strict", orch
assert orch.get("topology") == "subagent", orch
PY

# --- 2./3. `hook`-tier gate text: exactly one, and it is the ENFORCED one. --
gate_headings="$(grep -c '^# CRITICAL GATE' "$RULE" || true)"
[ "$gate_headings" = "1" ] || fail "exactly one '# CRITICAL GATE' heading expected in $RULE, got $gate_headings"
grep -qx '# CRITICAL GATE' "$RULE" \
    || fail "$RULE must carry the enforced (hook-tier) variant '# CRITICAL GATE' — no suffix"
for variant in '(advisory)' '(neutral)' '(runtime-partially enforced)'; do
    if grep -qF "# CRITICAL GATE $variant" "$RULE"; then
        fail "$RULE carries the non-enforced gate variant '# CRITICAL GATE $variant' (Claude resolves to the hook tier)"
    fi
done
# The enforced strict sentence (topology != primary -> the main chat is forbidden).
grep -qF 'MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.' "$RULE" \
    || fail "$RULE must carry the enforced strict gate sentence"
# ... and it must NOT claim the orchestrator IS the session entry (POS-2).
if grep -qF 'Session-Einstieg (`strict` verlangt das)' "$RULE"; then
    fail "$RULE claims POS-3 (orchestrator is the session entry) although the topology resolves to subagent"
fi

# --- 4. No orchestrator entry point in any settings document. --------------
for doc in .claude/settings.json .claude/settings.local.json opencode.json; do
    [ -e "$doc" ] || continue
    if grep -qF "default_agent" "$doc"; then
        echo "----- $doc -----"
        grep -nF "default_agent" "$doc"
        fail "$doc carries a default_agent entry point; POS-2 on Claude has none"
    fi
done

# --- 5. No orphan placeholders in the generated agents and rules. ----------
leftover="$(grep -rhoE '\{\{[A-Za-z][A-Za-z0-9_]*\}\}' .claude/agents .claude/rules 2>/dev/null | sort -u || true)"
[ -z "$leftover" ] || {
    echo "----- unresolved placeholders -----"
    printf '%s\n' "$leftover"
    fail "unresolved {{PLACEHOLDER}} in generated .claude/agents or .claude/rules"
}

echo "ASSERT OK (104-claude-strict-subagent): POS-2 on Claude — role emitted as subagent, enforced hook-tier gate text (one variant), no default_agent entry point, no orphan placeholders"
