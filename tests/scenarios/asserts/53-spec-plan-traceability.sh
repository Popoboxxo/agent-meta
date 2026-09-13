#!/bin/bash
# Scenario assert for 53-spec-plan-traceability
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (53-spec-plan-traceability): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (53-spec-plan-traceability): $*"
    exit 1
}

# The DoD presets live in the agent-meta checkout (submodule in real consumer
# projects). The harness temp project has none, so emulate the submodule layout
# for the validator's resolve_agent_meta_root() — otherwise the spec-driven
# preset cannot be resolved and the traceability checks downgrade to WARNING.
if [ ! -e ".agent-meta" ]; then
    ln -s "$REPO_ROOT" .agent-meta
fi

mkdir -p docs/specs docs/plans

# --- valid spec/plan pair -------------------------------------------------
cat > docs/specs/2026-01-01-trace-design.md <<'SPEC'
# Trace Demo — Spec

> Status: APPROVED (2026-01-01)

## Problem

Demo problem.

## Ziel

Demo goal.

## Nicht-Ziele

None.

## Interface Contracts

demo.py:demo() -> str

## Datenfluss

Input to output.

## Acceptance Criteria

1. Works.

## Offene Fragen

None.

## Trace-Anker: spec-id: SPEC-trace-demo
SPEC

cat > docs/plans/2026-01-01-trace.md <<'PLAN'
---
pipeline_stages:
  implement: 1
---

# Trace Demo Implementation Plan

> Status: geplant

**Goal:** Demonstrate traceability.
**Architecture:** Plain markdown.
**Tech Stack:** Markdown.
**Spec:** docs/specs/2026-01-01-trace-design.md

## Global Constraints

None.

## File Structure

- Create: docs/plans/2026-01-01-trace.md — demo plan

Trace anchor: SPEC-trace-demo

### Task 1: Do the thing

**Files:** Create: tests/test_trace_demo.py
**Interfaces:** Produces: demo()

- [ ] Step 1: write failing test for task-1
- [ ] Step 2: implement
- [ ] Step 3: run test for task-1 (pass)
- [ ] Step 4: commit
PLAN

valid_out="$(python3 "$REPO_ROOT/scripts/sync.py" --validate-spec-plan 2>&1)"
valid_rc=$?
if [ "$valid_rc" != "0" ]; then
    echo "$valid_out"
    fail "valid fixtures not clean (rc=$valid_rc)"
fi
if printf '%s\n' "$valid_out" | grep -q '\[ERR\]'; then
    echo "$valid_out"
    fail "valid fixtures produced ERROR findings"
fi

# --- invalid spec/plan pair ----------------------------------------------
cat > docs/plans/2026-01-02-broken.md <<'BROKEN'
# Broken Plan

**Spec:** docs/specs/does-not-exist-design.md

TODO

### Task 9: broken

**Files:** Create: tests/test_broken.py

- [ ] Step 1: implement
BROKEN

invalid_out="$(python3 "$REPO_ROOT/scripts/sync.py" --validate-spec-plan 2>&1)"
invalid_rc=$?
if [ "$invalid_rc" = "0" ]; then
    echo "$invalid_out"
    fail "invalid fixtures unexpectedly clean (rc=0)"
fi

# spec-plan-required/traceability come from the spec-driven preset -> ERROR
printf '%s\n' "$invalid_out" | grep -q '\[ERR\] \[spec_plan_required_sections\]' \
    || { echo "$invalid_out"; fail "required-sections ERROR missing"; }
printf '%s\n' "$invalid_out" | grep -q '\[ERR\] \[spec_plan_no_placeholder\]' \
    || { echo "$invalid_out"; fail "no-placeholder ERROR missing"; }
printf '%s\n' "$invalid_out" | grep -q '\[ERR\] \[spec_plan_traceability\]' \
    || { echo "$invalid_out"; fail "traceability ERROR missing"; }

echo "ASSERT OK (53-spec-plan-traceability): valid pair clean, invalid pair reports ERRORs"
