#!/bin/bash
# promptfoo custom-script provider: shells out to the real `claude` CLI,
# using this repo's actual generated .claude/rules/use-orchestrator.md as
# the system prompt. This tests whether agent-meta's GENERATED routing
# table (not a description of it) produces correct delegation decisions in
# a real Claude session.
#
# Isolation: `claude -p` still auto-discovers CLAUDE.md/.claude/rules from
# the invoking cwd even with --system-prompt-file (verified: run from
# inside this repo, the model knew the DoD-preset "rapid-prototyping",
# which only exists in agent-meta/CLAUDE.md, not in use-orchestrator.md).
# --bare would suppress that but requires ANTHROPIC_API_KEY (no OAuth),
# which isn't available here. Running from a throwaway tmp dir gets the
# same isolation without needing an API key.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROMPT="$1"

RUN_DIR="$(mktemp -d)"
trap 'rm -rf "$RUN_DIR"' EXIT

(
  cd "$RUN_DIR"
  claude -p \
    --system-prompt-file "$REPO_ROOT/.claude/rules/use-orchestrator.md" \
    --model haiku \
    "$PROMPT"
)
