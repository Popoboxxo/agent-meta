"""Issue #1344: OpenCode orchestrator dispatch vocabulary.

The generated OpenCode orchestrator must dispatch through
``subagent(agent="<named role>")`` — the only built-in subagent primitive on
that surface.  ``task(...)`` / ``route_intent`` are not OpenCode built-ins, and
a named role that cannot be resolved must fail closed to ``main_chat`` instead
of silently downgrading to ``general``.

Regression contract (data-driven, provider-agnostic):

* the wrong vocabulary lives in ``config/delegation-syntax.yaml`` and
  ``config/provider-capabilities.yaml`` — this test fails when it is reintroduced;
* every generic-template text change is gated by a PAL key that is truthy only
  for Opencode, so all other providers keep their 41dd69ac bytes;
* no generated provider output is written — rendering happens in ``tmp_path``.

Run: python3 -m pytest tests/test_opencode_dispatch_form_1344.py -q
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from tests.conftest import ALL_PROVIDERS  # noqa: E402

BASELINE = "41dd69ac"
# Every registered provider except the one owning the PAL gate. Derived from the
# central registry (issue #1240) instead of an eight-name copy, so a new
# provider joins these gate assertions automatically.
_NON_OPENCODE_PROVIDERS = tuple(p for p in ALL_PROVIDERS if p != "Opencode")

SYNTAX_FILE = REPO_ROOT / "config" / "delegation-syntax.yaml"
CAPS_FILE = REPO_ROOT / "config" / "provider-capabilities.yaml"


def _syntax() -> dict:
    return yaml.safe_load(SYNTAX_FILE.read_text(encoding="utf-8"))["delegation_syntax"]


def _caps() -> dict:
    return yaml.safe_load(CAPS_FILE.read_text(encoding="utf-8"))["capabilities"]


def _render_orchestrator(
    provider: str, project_root: Path, agent_meta_root: Path = REPO_ROOT
) -> str:
    """Render the orchestrator through the real per-role sync pipeline (tmp only)."""
    from scripts.lib.agent_sync import (
        _apply_content_pipeline,
        _build_provider_vars,
        _compose_role_content,
        _finalize_agent_content,
        _resolve_sync_targets,
    )
    from scripts.lib.config import build_variables, load_config
    from scripts.lib.log import SyncLog
    from scripts.lib.providers import load_providers_config

    project_root.mkdir(parents=True, exist_ok=True)
    config = load_config(agent_meta_root / ".meta-config" / "project.yaml")
    template = (agent_meta_root / "agents" / "1-generic" / "orchestrator.md").read_text(
        encoding="utf-8"
    )
    variables, _warnings = build_variables(config, agent_meta_root, project_root)
    provider_config = load_providers_config(agent_meta_root, config)
    log = SyncLog()
    pc, _role_map, overrides, target_dir = _resolve_sync_targets(
        provider, provider_config, agent_meta_root, project_root, config, True, log
    )
    assert pc is not None, f"{provider} provider config missing"

    source_path = overrides["orchestrator"]
    target_path = target_dir / "orchestrator.md"
    project_name = config.get("project", {}).get("name", "unknown")
    content, can_spawn, rel_source, source_version, description = _compose_role_content(
        source_path, provider, project_name, agent_meta_root, project_root,
        target_path, log, pc=pc,
    )
    details_dir = f".{provider.lower()}/pipeline-details"
    variables.setdefault("PIPELINE_DETAILS_DIR", details_dir)
    merged = _build_provider_vars(
        pc, provider, variables, agent_meta_root, config=config, active_set=frozenset()
    )
    merged.setdefault("PIPELINE_DETAILS_DIR", details_dir)
    content = _apply_content_pipeline(
        content, config, provider, merged, rel_source, None, agent_meta_root, log
    )
    return _finalize_agent_content(
        content, "orchestrator", "orchestrator.md", source_path, provider,
        provider_config, source_version, description, can_spawn, config,
        agent_meta_root, project_root, target_path, variables, False, log,
    )


@pytest.fixture(scope="module")
def opencode_rendered(tmp_path_factory: pytest.TempPathFactory) -> str:
    root = tmp_path_factory.mktemp("dispatch-1344")
    return _render_orchestrator("Opencode", root / "opencode")


def _dispatch_section(rendered: str) -> str:
    """§6 dispatch mechanics/delegation table — the dispatch examples."""
    start = rendered.index("## 6. Task decomposition & delegation")
    end = rendered.index("## 7. BARRIER protocol")
    return rendered[start:end]


# --------------------------------------------------------------------------
# AC-1 / AC-2: OpenCode dispatch form
# --------------------------------------------------------------------------


def test_opencode_dispatch_section_uses_subagent_only(opencode_rendered: str):
    section = _dispatch_section(opencode_rendered)
    assert "subagent(agent=" in section, section[:800]
    assert "task(" not in section, "stale task() dispatch in §6"
    assert "route_intent" not in section, "stale route_intent dispatch in §6"


def test_opencode_rendered_has_no_task_call_anywhere(opencode_rendered: str):
    """The persona HARD-REJECT example must not use the stale primitive (spec :19)."""
    assert "task(subagent_type=" not in opencode_rendered
    assert "route_intent(" not in opencode_rendered


def test_opencode_pipeline_notation_is_subagent_backed():
    notation = _syntax()["Opencode"]["pipeline_notation"]
    assert notation["task_fmt"] == 'subagent(agent="{agent}", prompt="{task}")'
    for key in ("loop_item", "parallel_item", "fanout_item", "sequential_item"):
        assert "subagent(agent=" in notation[key], key
    block = _syntax()["Opencode"]
    for key in ("delegate", "fanout", "parallel_group", "parallel_pattern"):
        assert "subagent(agent=" in block[key], key
        assert "task(" not in block[key], key


# --------------------------------------------------------------------------
# AC-3: fail-closed named-role resolution
# --------------------------------------------------------------------------


def test_opencode_fail_closed_escalation_present(opencode_rendered: str):
    section = opencode_rendered[
        opencode_rendered.index("## 11. Unknown intent protocol"):
        opencode_rendered.index("## 12. Few-shot patterns")
    ]
    assert "main_chat" in section
    assert "general" in section  # named explicitly as the forbidden downgrade
    assert "nie still" in section.lower() or "never silent" in section.lower()


def test_fail_closed_key_is_opencode_only():
    code = _syntax()["Opencode"]
    assert code.get("fail_closed_dispatch") == "true"
    assert "main_chat" in code["fallback"]
    caps = _caps()["Opencode"]
    assert caps.get("missing_role_fallback") == "main_chat"
    assert caps["native_agent_tools"] == ["subagent"]
    for provider, block in _syntax().items():
        if provider != "Opencode":
            assert "fail_closed_dispatch" not in block, provider
            assert "main_chat" not in str(block.get("fallback", "")), provider


# --------------------------------------------------------------------------
# AC-4: drift guard re-importing the wrong vocabulary fails
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["task_fmt", "loop_item", "parallel_item", "fanout_item", "sequential_item"])
def test_no_task_fmt_regression(key: str):
    assert "task(" not in _syntax()["Opencode"]["pipeline_notation"][key]


def test_capability_no_longer_declares_task_tool():
    caps = _caps()["Opencode"]
    assert "task" not in caps["native_agent_tools"]
    assert "task()" not in caps["description"]


# --------------------------------------------------------------------------
# AC-6: every other provider stays byte-identical to the baseline
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def baseline_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Full 41dd69ac tree in tmp via `git archive` (no checkout, no repo writes)."""
    import io
    import tarfile

    root = tmp_path_factory.mktemp("baseline-1344")
    archive = subprocess.run(
        ["git", "archive", BASELINE], cwd=REPO_ROOT,
        capture_output=True, check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(root)
    return root


#: Release-volatile metadata keys. The whole prefix (optional ``# `` comment
#: marker used by TOML-style renders, key name and ``generated-from`` source
#: path) is kept, so only the trailing version value is neutralized; a drifted
#: key, marker or path still fails the byte comparison.
_VERSION_META_LINE = re.compile(
    r"^(?P<prefix># )?(?P<key>version: |generated-from: [\w./-]+@)(?P<value>\S+)$",
    re.MULTILINE,
)
_NEUTRAL_VERSION = "<RELEASE_VERSION>"


def _neutralize_version_metadata(rendered: str) -> str:
    """Neutralize only the values of the ``version:`` / ``generated-from:`` lines.

    Analogous to ``_port_golden_meta_tokens`` in
    ``tests/test_template_slimming_equivalence.py:1432``: a coordinated version
    bump must not force a golden re-pin, but must not mask any other byte. Both
    comparison sides are normalized, leaving every non-metadata byte exact.
    """
    return _VERSION_META_LINE.sub(
        lambda match: (match.group("prefix") or "")
        + match.group("key")
        + _NEUTRAL_VERSION,
        rendered,
    )


@pytest.mark.parametrize("provider", _NON_OPENCODE_PROVIDERS)
def test_other_provider_render_byte_identical_to_baseline(
    provider: str, tmp_path: Path, baseline_root: Path
):
    """AC-6: the PAL gate is absent for other providers, so their rendered
    orchestrator is byte-for-byte the 41dd69ac artifact (not just config data),
    except for the two coordinated version-metadata values."""
    now = _render_orchestrator(provider, tmp_path / "now", REPO_ROOT)
    base = _render_orchestrator(provider, tmp_path / "base", baseline_root)
    assert _neutralize_version_metadata(now) == _neutralize_version_metadata(base)


def test_baseline_other_providers_used_stale_form(baseline_root: Path, tmp_path: Path):
    """Guard the guard: the baseline really did carry the old form elsewhere."""
    base = _render_orchestrator("Claude", tmp_path / "claude-base", baseline_root)
    now = _render_orchestrator("Claude", tmp_path / "claude-now", REPO_ROOT)
    assert _neutralize_version_metadata(base) == _neutralize_version_metadata(now)


def test_non_opencode_render_keeps_legacy_dispatch_vocabulary(tmp_path):
    """The PAL gate is closed for Claude: legacy dispatch survives verbatim."""
    claude = _render_orchestrator("Claude", tmp_path / "claude")
    assert "subagent(agent=" not in claude
    assert "background(agent=" in claude  # unchanged Claude PAL delegate syntax


def test_pal_dispatch_reject_call_is_gated():
    """New template text is a PAL key: Opencode-only, absent elsewhere."""
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    engine = DelegationSyntaxEngine(config_dir=REPO_ROOT / "config")
    probe = "{{PAL_DISPATCH_REJECT_CALL}}"
    assert engine.apply(probe, "Opencode") == '`subagent(agent="orchestrator")`'
    for provider in _NON_OPENCODE_PROVIDERS:
        assert engine.apply(probe, provider) == '`task(subagent_type="orchestrator")`', provider


def test_pal_fail_closed_block_is_gated():
    """The fail-closed §11 rule renders only for the Opencode binding."""
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    engine = DelegationSyntaxEngine(config_dir=REPO_ROOT / "config")
    probe = "{{#if PAL_FAIL_CLOSED_DISPATCH}}\nFAIL-CLOSED-RULE\n{{/if}}\n"
    assert "FAIL-CLOSED-RULE" in engine.apply(probe, "Opencode")
    for provider in _NON_OPENCODE_PROVIDERS:
        assert "FAIL-CLOSED-RULE" not in engine.apply(probe, provider), provider
