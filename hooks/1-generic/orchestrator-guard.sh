#!/bin/bash
# hook: orchestrator-guard
# version: 1.0.0
# event: PreToolUse
# description: Blocks direct worker subagent calls from main chat — enforces Orchestrator-First routing
# enabled_by_default: false

# Receives hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block (stdout shown to the agent as feedback).

# python3 required for JSON parsing
command -v python3 &>/dev/null || exit 0

# --------------------------------------
# Parse hook input JSON from stdin
# --------------------------------------
read -r -d '' _PARSE_INPUT <<'PYEOF'
import json, sys, os

d = json.load(sys.stdin)
tool_name = d.get('tool_name', '')

# Extract subagent identifier from task tool calls.
# Opencode uses 'subagent_type', other providers may use 'subagent_name' or 'subagent'.
tool_input = d.get('tool_input', {})
if isinstance(tool_input, dict):
    subagent = (tool_input.get('subagent_type', '') or
                tool_input.get('subagent_name', '') or
                tool_input.get('subagent', ''))
else:
    subagent = ''

# Determine caller context:
# 1. AGENT_NAME env var (set for subagent processes)
# 2. Fallback: check if tool is task() → likely main chat invoking subagent
agent_name = os.environ.get('AGENT_NAME', '')

print(tool_name)
print(subagent)
print(agent_name)
PYEOF

_parsed=$(python3 -c "$_PARSE_INPUT" 2>/dev/null)
TOOL_NAME=$(printf '%s' "$_parsed" | sed -n '1p')
SUBAGENT=$(printf '%s' "$_parsed" | sed -n '2p')
AGENT_NAME=$(printf '%s' "$_parsed" | sed -n '3p')

# --------------------------------------
# Only intercept task() / Agent() tool calls
# --------------------------------------
# Support both Opencode (task) and Claude (Agent) tool names
case "$TOOL_NAME" in
    task|Task|Agent) ;;
    *) exit 0 ;;
esac

# No subagent extracted → allow (not a delegation call)
[ -n "$SUBAGENT" ] || exit 0

# --------------------------------------
# Orchestrator context → allow everything
# --------------------------------------
# If we're running inside the orchestrator subagent, all delegations are allowed.
if [ "$AGENT_NAME" = "orchestrator" ]; then
    exit 0
fi

# --------------------------------------
# Direct-dispatch exceptions (main chat only)
# --------------------------------------
# These agents are permitted direct calls from the main chat
# per "Orchestrator — Universal Router" policy:
#   git                → single git commands
#   agent-meta-manager → pure agent-meta operations
#   feedback           → issue creation
#   documenter         → session-end knowledge capture
case "$SUBAGENT" in
    orchestrator|git|agent-meta-manager|feedback|documenter)
        exit 0
        ;;
esac

# --------------------------------------
# Block: main chat calling a worker directly
# --------------------------------------
cat <<BLOCKED
╔══════════════════════════════════════════════════════════════╗
║  Orchestrator Guard — Direct Worker Call Blocked            ║
╠══════════════════════════════════════════════════════════════╣
║  The main chat must NOT call worker agents directly.        ║
║  All worker invocations must go through @orchestrator.      ║
║                                                            ║
║  Blocked: task(subagent_type="${SUBAGENT}", ...)           ║
║                                                            ║
║  Instead, delegate to the orchestrator:                    ║
║    @orchestrator <your task description>                   ║
║                                                            ║
║  Direct-dispatch exceptions (main chat → agent):           ║
║    git                — single git commands                ║
║    agent-meta-manager — sync, upgrade, meta-config         ║
║    feedback           — issue creation                     ║
║    documenter         — session-end knowledge capture      ║
║                                                            ║
║  User override: "Nicht delegieren", "Im Hauptchat bitte",  ║
║  "Kein Orchestrator", "Ohne Orchestrator"                  ║
║  (triggers main-chat handling — hook not involved)         ║
╚══════════════════════════════════════════════════════════════╝
BLOCKED

exit 2
