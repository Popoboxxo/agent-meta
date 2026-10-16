"""IC-15 Nr. 10 / AC-10 (F-14): Continue rule files must carry lazy-load
frontmatter (``alwaysApply: false`` + ``description``) so the runtime no longer
pushes all ``.continue/rules/*.md`` (18,591 B, study §3.8) into every request,
and the generated ``.continue/rules/project-context.md`` must not ship
unresolved ``{{VAR}}`` placeholders.

Red (before the fix): Continue rule files start at the H1 (no frontmatter, so
``alwaysApply`` is undefined -> always active) and ``project-context.md`` still
contains ``{{PLATFORM}}``/``{{BUILD_COMMAND}}``/... .
Green: ``sync_rules`` injects the frontmatter driven by the
``rules-always-apply`` capability (no provider-name literal) and the Continue
context writer omits unresolved-placeholder lines.

Run: python -m pytest tests/test_continue_rule_frontmatter.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables, load_config  # noqa: E402
from lib.consistency import active_set_refs as asr  # noqa: E402
from lib.context import sync_context_for_provider  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402
from lib.rules import sync_rules  # noqa: E402
from lib.sync_pipeline import converge_managed_block_context  # noqa: E402

_RULES_DIR = ".continue/rules"
_CONTINUE_PC = {
    "Continue": {
        "rules_dir": _RULES_DIR,
        "context_file": f"{_RULES_DIR}/project-context.md",
        "context_template": "templates/configs/CONTINUE.project-template.md",
        "capabilities": ["rules-always-apply"],
    }
}
# A provider WITHOUT the capability must be left untouched (capability-driven).
_PLAIN_PC = {"Other": {"rules_dir": ".rules"}}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _rule_root(tmp_path: Path) -> Path:
    root = tmp_path / "agent-meta"
    _write(
        root / "rules" / "1-generic" / "branch-guard.md",
        "# Branch-Guard\n\nUse feature branches, never edit main directly.\n",
    )
    _write(
        root / "rules" / "1-generic" / "language.md",
        "# Language Rules\n\nUser communication is German, code is English.\n",
    )
    return root


def test_continue_rules_gain_lazy_frontmatter(tmp_path):
    """Every Continue rule file gets ``alwaysApply: false`` + ``description``."""
    root = _rule_root(tmp_path)
    project = tmp_path / "project"

    sync_rules(
        root, project, {}, SyncLog(), dry_run=False, variables={},
        rules_dir=_RULES_DIR, provider="Continue", provider_config=_CONTINUE_PC,
    )

    for name in ("branch-guard.md", "language.md"):
        text = (project / _RULES_DIR / name).read_text(encoding="utf-8")
        assert text.startswith("---\n"), name
        assert "alwaysApply: false" in text, name
        assert "description:" in text, name


def test_frontmatter_is_capability_driven_not_provider_literal(tmp_path):
    """A provider without ``rules-always-apply`` gets no injected frontmatter."""
    root = _rule_root(tmp_path)
    project = tmp_path / "project"

    sync_rules(
        root, project, {}, SyncLog(), dry_run=False, variables={},
        rules_dir=".rules", provider="Other", provider_config=_PLAIN_PC,
    )

    text = (project / ".rules" / "branch-guard.md").read_text(encoding="utf-8")
    assert text.startswith("# Branch-Guard")
    assert "alwaysApply" not in text


def _drop_meta_vars(variables: dict) -> dict:
    """Remove the project-metadata vars a bare consumer project may omit.

    Mirrors the provider-matrix scratch project in tests/test_ac01_render_identity.py
    (only PROJECT_NAME/PROJECT_PREFIX set); study §3.8 measured these keys unset.
    """
    fresh = dict(variables)
    for key in ("PLATFORM", "RUNTIME", "BUILD_COMMAND", "TEST_COMMAND"):
        fresh.pop(key, None)
    return fresh


def test_continue_context_has_no_unresolved_placeholders(tmp_path):
    """project-context.md never ships ``{{VAR}}`` placeholders (study §3.8)."""
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, _REPO_ROOT)
    variables = _drop_meta_vars(variables)
    provider_config = load_providers_config(_REPO_ROOT)
    context_file = provider_config["Continue"]["context_file"]

    log = SyncLog()
    sync_context_for_provider(
        _REPO_ROOT, tmp_path, config, variables, log,
        dry_run=False, provider="Continue", provider_config=provider_config,
    )
    converge_managed_block_context(
        tmp_path, context_file, variables, log, agent_meta_root=_REPO_ROOT,
    )

    text = (tmp_path / context_file).read_text(encoding="utf-8")
    assert "{{PLATFORM}}" not in text
    assert "{{BUILD_COMMAND}}" not in text
    assert "{{RUNTIME}}" not in text
    assert "{{TEST_COMMAND}}" not in text

    findings = asr.check_unresolved_placeholder(tmp_path, ["Continue"], {}, None)
    assert findings == [], [f.message for f in findings]
