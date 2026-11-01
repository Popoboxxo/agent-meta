"""Pins for the ``test-environments`` recipe in ``agent-meta-manager`` (Task 12).

The recipe's YAML example must be valid for ``lib.test_environments`` and,
written through the admin server's section endpoints, round-trip byte-for-byte
with the UI write path (AC-ENV-14).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _te_admin_helpers import _handler, _post  # noqa: E402
from lib.test_environments import collect_test_environment_errors  # noqa: E402

SRC = (REPO_ROOT / "agents" / "1-generic" / "agent-meta-manager.md").read_text(
    encoding="utf-8"
)
HEADING = re.search(r"(?m)^## \d+[a-z]?\. Test environments.*$", SRC)


def test_version_is_1_27_0():  # AC-ENV-13
    assert 'version: "1.27.0"' in SRC


def test_recipe_steps_present():
    assert HEADING
    recipe = SRC[HEADING.start():].split("\n## ", 1)[0]
    for s in (
        "Ask which kind",
        "local, remote or both",
        "`environments:`",
        "secret: true",
        "without a value",
        "token-env",
        "only the NAME",
        "source .meta-config/env.sh",
        "never post the value in the chat",
        "sync.py",
        "--validate",
        "`environments:` (env-var definitions)",
        "`test-environments:` (targets)",
    ):
        assert s in recipe, s


def test_confirmation_table_row():
    assert re.search(r"(?m)^\| Enable remote test environments .*Behavior change", SRC)


def test_recipe_example_is_valid_and_has_parity_with_ui_write(tmp_path):  # AC-ENV-14
    recipe = SRC[HEADING.start():].split("\n## ", 1)[0]
    example = yaml.safe_load(re.search(r"```yaml\n(.*?)```", recipe, re.S).group(1))
    assert collect_test_environment_errors(example) == []
    h = _handler(tmp_path)
    for section in ("environments", "test-environments"):  # reference target first
        _post(h, section, example[section])
    persisted = h.config_manager.read("project")
    assert {k: persisted[k] for k in example} == example
