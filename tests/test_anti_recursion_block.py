"""IC-18 no. 6 (Task 1.14, AC-49 part): ``ANTI_RECURSION_BLOCK`` from data ∩ ActiveSet.

The roles a worker may point to from its context come from
``config/role-defaults.yaml`` (``anti_recursion.reference_roles``) intersected
with ``ActiveSet.roles`` -- no string literal in the builder.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts.lib.active_set import compute_active_set
from scripts.lib.config import build_variables
from tests.active_set_render import REPO_ROOT, all_roles, default_config, fixture_config

_FULL_TEXT = (
    "Anti-Recursion: NIEMALS zurück an orchestrator delegieren. "
    "Nur tester/documenter/requirements/validator aus Kontext verweisen."
)


def _block(config: dict, tmp_path: Path) -> str:
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    variables, _ = build_variables(config, REPO_ROOT, tmp_path, active_set=active)
    return variables["ANTI_RECURSION_BLOCK"]


def _reference_roles() -> list:
    data = yaml.safe_load((REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8"))
    return list(data["anti_recursion"]["reference_roles"])


def test_reference_roles_are_data_and_known_roles():
    roles = _reference_roles()
    assert roles == ["tester", "documenter", "requirements", "validator"]
    assert set(roles) <= set(all_roles())


def test_p10_block_names_no_inactive_role(tmp_path):
    # p10 has tester/documenter/requirements but no validator.
    block = _block(fixture_config("p10"), tmp_path)
    assert "validator" not in block
    assert block == (
        "Anti-Recursion: NIEMALS zurück an orchestrator delegieren. "
        "Nur tester/documenter/requirements aus Kontext verweisen."
    )


def test_default_block_drops_gated_validator(tmp_path):
    # Default: the validator gate is off.
    assert "validator" not in _block(default_config(), tmp_path)


def test_all_roles_block_is_unchanged_text(tmp_path):
    config = default_config()
    config["roles"] = all_roles()
    assert _block(config, tmp_path) == _FULL_TEXT


def test_no_active_reference_role_drops_the_sentence(tmp_path):
    config = default_config()
    config["roles"] = ["orchestrator", "developer", "git"]
    assert _block(config, tmp_path) == "Anti-Recursion: NIEMALS zurück an orchestrator delegieren."


def test_builder_has_no_role_literal():
    src = (REPO_ROOT / "scripts" / "lib" / "config.py").read_text(encoding="utf-8")
    assert "tester/documenter/requirements/validator" not in src
