"""Tests for the agent-eval framework (issue #535, resolving findings #523).

Covers:
- provider wrappers: --agent parsing, exit 2 on unknown role (W6),
  frontmatter stripping for non-orchestrator Claude roles (H3)
- catalog hygiene: unique ids across catalogs, behavioral cases carry
  role + at least one assert criterion
- promptfoo SoT: generated config is fresh and idempotent (W3/W4)
"""

import json
import os
import subprocess
import sys
import tempfile
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


def test_claude_wrapper_orchestrator_uses_rendered_agent_file(tmp_path):
    """IC-13: the orchestrator prompt is the rendered, frontmatter-stripped
    .claude/agents/orchestrator.md (not the use-orchestrator.md stub). A PATH
    stub for `claude` echoes the system-prompt file; no LLM call happens."""
    rendered = _REPO_ROOT / ".claude" / "agents" / "orchestrator.md"
    if not rendered.is_file():
        pytest.skip("rendered orchestrator missing (run sync.py)")
    stub = tmp_path / "claude"
    stub.write_text(
        '#!/bin/bash\nwhile [[ $# -gt 0 ]]; do\n'
        '  if [[ "$1" == "--system-prompt-file" ]]; then cat "$2"; exit 0; fi\n'
        '  shift\ndone\nexit 3\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        ["bash", str(EVAL_DIR / "provider-claude.sh"), "--agent", "orchestrator", "p"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    text = rendered.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1] if text.startswith("---") else text
    assert body.strip() in result.stdout
    assert not result.stdout.startswith("---")


def test_claude_wrapper_reports_auth_failure(tmp_path):
    """Bug #977: a failing `claude` invocation must not be swallowed by `set -e`.

    The wrapper has to surface claude's own diagnostic ("Not logged in") plus a
    hint and exit 2 — not die with exit 1 and no diagnosis. The fake `claude`
    earlier in PATH shadows the real CLI, so no LLM call happens.

    Self-sufficient: the wrapper copy, the minimal rendered orchestrator and the
    fake CLI all live in ``tmp_path``, so the test also passes on a clean
    checkout without a prior ``sync.py`` run.
    """
    repo = tmp_path / "repo"
    wrapper = repo / "tests" / "routing-llm-eval" / "provider-claude.sh"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text(
        (EVAL_DIR / "provider-claude.sh").read_text(encoding="utf-8"), encoding="utf-8")
    agents = repo / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "orchestrator.md").write_text(
        "---\nname: orchestrator\n---\nMinimal orchestrator prompt.\n", encoding="utf-8")
    stub = tmp_path / "bin" / "claude"
    stub.parent.mkdir()
    stub.write_text('#!/bin/bash\necho "Not logged in" >&2\nexit 1\n', encoding="utf-8")
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{stub.parent}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        ["bash", str(wrapper), "--agent", "orchestrator", "test prompt"],
        capture_output=True, text=True, env=env, cwd=str(repo), timeout=60,
    )
    assert result.returncode == 2, (
        f"expected exit 2 on auth failure, got {result.returncode}: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "claude invocation failed" in result.stderr, f"stderr={result.stderr!r}"
    assert "Not logged in" in result.stderr, f"stderr={result.stderr!r}"


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
        if not str(case.get("id", "")).startswith(("b2-", "b3-", "b5-", "b6-", "b7-")):
            continue
        assert case.get("role"), f"{case['id']}: behavioral case without role"
        has_assert = any(
            case.get(k) for k in ("expected_any", "expected_all", "forbidden", "expected")
        )
        assert has_assert, f"{case['id']}: no assert criterion"
        if case.get("forbidden") or case.get("expected_any"):
            # B2/B3/B7 grade on substrings, never on one-word equals; keep the
            # literals plain — promptfoo's `icontains-any` matches literally.
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


def test_generated_promptfoo_providers_use_exec_id_form():
    """promptfoo identifies `exec` providers via ``id: exec:<script>``.

    A bare ``id: exec`` plus a separate ``command`` array is rejected by
    ``promptfoo validate`` ("Could not identify provider: exec"). The script
    path in the id is resolved relative to the config file's directory.
    """
    data = yaml.safe_load(
        (EVAL_DIR / "promptfooconfig.generated.yaml").read_text(encoding="utf-8")
    )
    assert data["providers"], "no providers in generated config"
    for provider in data["providers"]:
        assert "command" not in provider, (
            f"provider {provider!r} must not carry a command array (bug #977)"
        )
        assert provider["id"].startswith("exec:"), (
            f"provider id {provider['id']!r} must be 'exec:<script>' (bug #977)"
        )
        script = EVAL_DIR / provider["id"].split(":", 1)[1]
        assert script.exists(), f"provider script missing: {script}"


def test_generated_promptfoo_config_is_fresh_and_valid():
    gen = _REPO_ROOT / "scripts" / "gen_promptfoo_config.py"
    check = subprocess.run(
        ["python3", str(gen), "--check"], capture_output=True, text=True, cwd=str(_REPO_ROOT)
    )
    assert check.returncode == 0, f"stale generated config: {check.stderr}"

    raw = (EVAL_DIR / "promptfooconfig.generated.yaml").read_text(encoding="utf-8")
    # AC-18: the generated file carries the GENERATED header ("do not edit by hand").
    assert "do not edit by hand" in raw, "missing GENERATED header"
    data = yaml.safe_load(raw)
    assert data["providers"], "no providers in generated config"
    for provider in data["providers"]:
        # W4: promptfoo appends the rendered prompt as the last argv element; it
        # must never be embedded in the provider invocation itself.
        assert "{{prompt}}" not in provider["id"], "W4: no inline {{prompt}} allowed"
        assert "{{prompt}}" not in json.dumps(provider), "W4: no inline {{prompt}} allowed"
    assert len(data["tests"]) >= len(_all_cases()) - 1, "config lost cases during merge"


def test_generated_routing_catalog_is_fresh():
    """AC-17: `catalog.generated.yaml` must be a byte-exact regeneration of
    `config/role-defaults.yaml` — regenerate into a temp dir and compare.
    A changed `signal_keywords` source without regeneration fails here."""
    gen = _REPO_ROOT / "scripts" / "gen_routing_llm_eval_catalog.py"
    committed = EVAL_DIR / "catalog.generated.yaml"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "catalog.generated.yaml"
        result = subprocess.run(
            [sys.executable, str(gen), "--out", str(out)],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=120,
        )
        assert result.returncode == 0, result.stderr
        assert out.read_bytes() == committed.read_bytes(), (
            "catalog.generated.yaml is stale — regenerate with "
            "python3 scripts/gen_routing_llm_eval_catalog.py"
        )


def test_structured_sidecar_contract_shape():
    """B1: opencode sidecar JSON must expose the fields behavioral asserts need."""
    expected_keys = {"provider", "role", "stream", "final_text", "event_counts", "tool_events", "spawn_attempts"}
    wrapper = (EVAL_DIR / "provider-opencode.sh").read_text(encoding="utf-8")
    for key in expected_keys:
        assert f'"{key}"' in wrapper, f"sidecar field {key!r} not emitted"
