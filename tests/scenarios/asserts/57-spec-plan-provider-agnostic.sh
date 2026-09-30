#!/bin/bash
# Scenario assert for 57-spec-plan-provider-agnostic
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (57-spec-plan-provider-agnostic): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (57-spec-plan-provider-agnostic): $*"
    exit 1
}

# (a) Every configured provider receives all four gated rules in its own
#     delivery channel.
for rule in spec-plan-workflow brainstorming-gate writing-plans plan-ledger; do
    [ -f ".claude/skills/$rule/SKILL.md" ] \
        || fail "Claude gated rule '$rule' missing"
    [ -f ".opencode/skills/$rule/SKILL.md" ] \
        || fail "Opencode gated rule '$rule' missing"
    [ -f ".gemini/rules/$rule.md" ] \
        || fail "Gemini gated rule '$rule' missing"
done

# (b) Provider-agnostic content: the delivered rule bodies are identical across
#     providers and contain no provider literals. Also verify the SOURCE
#     templates in the agent-meta checkout — the four gated rules plus the
#     agent templates this feature touches — stay provider-literal-free.
python3 - "$REPO_ROOT" <<'PY' || fail "provider-agnostic content check failed"
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
root = Path(".")

PROVIDERS = (
    "Claude", "Gemini", "Opencode", "Codex", "KimiCode", "Kimi",
    "Mammouth", "Continue", "Copilot", "ZCode", "Antigravity", "Cursor",
)
RULES = ("spec-plan-workflow", "brainstorming-gate", "writing-plans", "plan-ledger")
AGENT_TEMPLATES = ("orchestrator", "planner", "concept-specifier", "explorer")


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return text


problems = []
for rule in RULES:
    claude = body(root / ".claude" / "skills" / rule / "SKILL.md")
    opencode = body(root / ".opencode" / "skills" / rule / "SKILL.md")
    gemini = body(root / ".gemini" / "rules" / f"{rule}.md")
    if not (claude == opencode == gemini):
        problems.append(f"{rule}: delivered bodies differ across providers")
    for name in PROVIDERS:
        if re.search(r"\b" + re.escape(name) + r"\b", claude):
            problems.append(f"{rule}: provider literal {name!r} in delivered body")

source_paths = [
    *(repo / "rules" / "1-generic" / f"{rule}.md" for rule in RULES),
    *(repo / "agents" / "1-generic" / f"{agent}.md" for agent in AGENT_TEMPLATES),
]
for path in source_paths:
    source = path.read_text(encoding="utf-8")
    for name in PROVIDERS:
        if re.search(r"\b" + re.escape(name) + r"\b", source):
            problems.append(
                f"{path.relative_to(repo)}: provider literal {name!r} in source"
            )

if problems:
    print("\n".join(problems))
    sys.exit(1)
PY

echo "ASSERT OK (57-spec-plan-provider-agnostic): per-provider rules, shared content, no literals"
