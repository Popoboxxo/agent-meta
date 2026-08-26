"""Tests for the agent-eval framework (issue #535, resolving findings #523).

Covers:
- provider wrappers: --agent parsing, exit 2 on unknown role (W6),
  frontmatter stripping for non-orchestrator Claude roles (H3)
- catalog hygiene: unique ids across catalogs, behavioral cases carry
  role + at least one assert criterion
- promptfoo SoT: generated config is fresh and idempotent (W3/W4)
"""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = _REPO_ROOT / "tests" / "routing-llm-eval"
_BASH = "bash"


def _run_provider(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(EVAL_DIR / script), *args],
        input="",
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=60,
    )


# --- wrappers -------------------------------------------------------------


@pytest.mark.parametrize("script", ["provider-claude.sh", "provider-opencode.sh"])
def test_wrapper_exit_2_on_unknown_role(script):
    """W6: a typo'd role must fail loudly (exit 2) BEFORE any CLI invocation."""
    result = _run_provider(script, "--agent", "does-not-exist-role", "test prompt")
    assert result.returncode == 2, f"stderr={result.stderr}"
    assert "unknown or missing role" in result.stderr


def test_claude_wrapper_strips_frontmatter_for_non_orchestrator():
    """H3: the system prompt for non-orchestrator roles must not contain
    YAML frontmatter — verify by inspecting the stripped copy logic via a
    dry parse of the wrapper script (no CLI call needed)."""
    script = (EVAL_DIR / "provider-claude.sh").read_text(encoding="utf-8")
    assert "frontmatter" in script.lower()
    assert "/^---[[:space:]]*$/" in script, "frontmatter-stripping awk missing"


# --- catalogs --------------------------------------------------------------


def _all_cases() -> list[tuple[str, dict]]:
    cases = []
    for name in ("catalog.generated.yaml", "catalog.manual.yaml", "catalog.behavior.yaml"):
        path = EVAL_DIR / name
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for case in data.get("cases", []):
            cases.append((name, case))
    return cases


def test_catalog_ids_unique_across_files():
    seen = {}
    for name, case in _all_cases():
        cid = case.get("id")
        assert cid, f"{name}: case without id"
        assert cid not in seen, f"duplicate id {cid!r}: {seen[cid]} vs {name}"
        seen[cid] = name


def test_behavioral_cases_have_role_and_asserts():
    for name, case in _all_cases():
        if not str(case.get("id", "")).startswith(("b2-", "b3-", "b5-", "b6-")):
            continue
        assert case.get("role"), f"{case['id']}: behavioral case without role"
        has_assert = any(
            case.get(k) for k in ("expected_any", "expected_all", "forbidden", "expected")
        )
        assert has_assert, f"{case['id']}: no assert criterion"
        if case.get("forbidden") or case.get("expected_any"):
            # B2/B3 rely on substring/regex semantics, never on one-word equals
            assert case.get("prompt"), f"{case['id']}: raw prompt required"


def test_routing_cases_keep_equals_semantics():
    """Legacy routing cases (kw-/mkw-/gen-/dis-/neg-/amb-/drift-) grade by
    exact normalized one-word match on `pipeline` — except `neg-`/`amb-`
    cases, which by construction have no single correct pipeline (neg-:
    none should match; amb-: several are equally valid) and grade on
    `expected: [...]` instead; `pipeline: null` there is correct data, not
    a missing field."""
    for name, case in _all_cases():
        cid = str(case.get("id", ""))
        prefix = cid.split("-")[0]
        if prefix in ("kw", "mkw", "gen", "dis", "drift"):
            assert case.get("pipeline"), f"{cid}: routing case without pipeline"
            assert not case.get("prompt"), f"{cid}: legacy case must use task wrap"
        elif prefix in ("neg", "amb"):
            assert case.get("expected"), f"{cid}: {prefix} case without expected"
            assert not case.get("prompt"), f"{cid}: legacy case must use task wrap"


# --- promptfoo config generation (W3/W4) -----------------------------------


def test_generated_promptfoo_config_is_fresh_and_valid():
    gen = _REPO_ROOT / "scripts" / "gen_promptfoo_config.py"
    check = subprocess.run(
        ["python3", str(gen), "--check"], capture_output=True, text=True, cwd=str(_REPO_ROOT)
    )
    assert check.returncode == 0, f"stale generated config: {check.stderr}"

    data = yaml.safe_load((EVAL_DIR / "promptfooconfig.generated.yaml").read_text(encoding="utf-8"))
    assert data["providers"], "no providers in generated config"
    for provider in data["providers"]:
        command = " ".join(provider["command"])
        assert "{{prompt}}" not in command, "W4: no inline {{prompt}} allowed"
    assert len(data["tests"]) >= len(_all_cases()) - 1, "config lost cases during merge"


def test_structured_sidecar_contract_shape():
    """B1: opencode sidecar JSON must expose the fields behavioral asserts need."""
    expected_keys = {"provider", "role", "stream", "final_text", "event_counts", "tool_events", "spawn_attempts"}
    wrapper = (EVAL_DIR / "provider-opencode.sh").read_text(encoding="utf-8")
    for key in expected_keys:
        assert f'"{key}"' in wrapper, f"sidecar field {key!r} not emitted"
