"""Tests for the Hermes skill-pack export (scripts/hermes_export.py, issue #527).

Covers:
- stdlib YAML emitter: round-trip, escaping, empty collections, safe keys
- abstract tier resolution: no model ID may ever leak into the export
- export_skill_pack against a synthetic mini agent-meta root (fixture):
  discovery filters (deprecated / underscore-prefixed), SKILL.md format,
  manifest structure, dry-run, role filter, tier overrides, idempotency
- export-config loading (JSON, YAML, error paths)
- CLI main() wiring (real run, dry-run, failure exit code)
- integration smoke against the real agent-meta repo (2 roles)

Note on model-ID scanning: for the synthetic fixture the whole pack is
scanned (fixture content is fully controlled). For the real-repo smoke only
manifest.yaml and the SKILL.md files are scanned — rendered persona prose
inherits example model IDs from source templates (e.g.
agents/1-generic/agent-meta-manager.md lines with model-override-all
examples), byte-identical to the standalone/ export by design.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

import scripts.hermes_export as hermes_export

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

# Concrete model IDs of every provider family currently listed in
# config/tier-presets.yaml — the export must contain none of them.
_MODEL_ID_RE = re.compile(
    r"claude-(?:haiku|sonnet|opus|fable)[a-z0-9.\-]*"
    r"|gemini-\d[\w.\-]*"
    r"|gpt-\d[\w.\-]*"
    r"|glm-\d[\w.\-]*"
    r"|kimi-k\d[\w.\-]*"
    r"|deepseek-[\w.\-]*"
    r"|qwen\d?[\w.\-]*"
    r"|mimo-v\d[\w.\-]*"
    r"|opencode-go/[\w./\-]*"
)


def _write_template(
    path: Path,
    role: str,
    description: str,
    *,
    deprecated: bool = False,
) -> None:
    """Write a minimal 1-generic agent template."""
    fm_lines = [
        "---",
        f"name: template-{role}",
        'version: "1.0.0"',
        f'description: "{description}"',
        f'hint: "{role} hint"',
        "tools:",
        "  - Bash",
    ]
    if deprecated:
        fm_lines.append("deprecated: true")
    fm_lines.append("---")
    path.write_text(
        "\n".join(fm_lines) + f"\n\n# {role}\n\nDo {role} things.\n",
        encoding="utf-8",
    )


def _make_mini_meta(tmp_path: Path, *, alpha_model: str = "fast") -> Path:
    """Build a synthetic agent-meta root.

    alpha: active, full role-defaults metadata (tier ``alpha_model``);
    gamma: active, NO role-defaults entry (frontmatter fallback);
    beta: deprecated template; _reserved: underscore resource.
    """
    root = tmp_path / "meta"
    generic = root / "agents" / "1-generic"
    generic.mkdir(parents=True)
    (root / "config").mkdir()
    (root / "VERSION").write_text("9.9.9-test", encoding="utf-8")

    _write_template(generic / "alpha.md", "alpha", "Alpha test role.")
    _write_template(generic / "beta.md", "beta", "Beta test role.", deprecated=True)
    _write_template(generic / "gamma.md", "gamma", "Gamma standalone description.")
    (generic / "_reserved.md").write_text("reserved\n", encoding="utf-8")

    (root / "config" / "role-defaults.yaml").write_text(
        "roles:\n"
        f"  alpha:\n"
        f"    model: {alpha_model}\n"
        "    description: Alpha role description.\n"
        "    routing:\n"
        "      intent_keywords:\n"
        "      - Alpha\n"
        "      - Test\n"
        "    handoff:\n"
        "      input_contracts:\n"
        "      - task-spec-v1\n"
        "      output_contract: dev-result-v1\n"
        "      input_schema: schemas/handoffs/task-spec.schema.json\n"
        "  beta:\n"
        "    model: powerful\n"
        "    description: Deprecated beta.\n"
        "  ghost:\n"
        "    model: nano\n"
        "    description: Role without a template.\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture()
def mini_meta(tmp_path: Path) -> Path:
    """Synthetic agent-meta root (see _make_mini_meta).

    Each test gets its own tmp_path, i.e. its own root path — deliberate,
    because lib loaders (load_roles_config) are process-lifetime cached per
    root (#553) and must not leak state across tests.
    """
    return _make_mini_meta(tmp_path)


def _scan_model_ids(directory: Path) -> list[str]:
    """Return all model-ID-looking matches across the files under a pack."""
    hits: list[str] = []
    for file in sorted(directory.rglob("*")):
        if not file.is_file():
            continue
        text = file.read_text(encoding="utf-8")
        hits.extend(f"{file.name}: {match}" for match in _MODEL_ID_RE.findall(text))
    return hits


# ===========================================================================
# stdlib YAML emitter
# ===========================================================================

class TestYamlEmitter:
    def test_scalar_quoting(self) -> None:
        assert (
            hermes_export._yaml_scalar('say "hi"')
            == '"say \\"hi\\""'
        )
        assert (
            hermes_export._yaml_scalar("back\\slash\nline")
            == '"back\\\\slash\\nline"'
        )

    def test_bare_vs_quoted_key(self) -> None:
        assert hermes_export._yaml_key("code-reviewer") == "code-reviewer"
        assert hermes_export._yaml_key("agent-meta-version") == "agent-meta-version"
        assert hermes_export._yaml_key("with space") == '"with space"'
        assert hermes_export._yaml_key("") == '""'

    def test_roundtrip_structure(self) -> None:
        data = {
            "version": "1.2.3",
            "format": "hermes-skillpack",
            "tier-order": ["nano", "fast", "balanced", "powerful", "max"],
            "empty-list": [],
            "empty-map": {},
            "nothing": None,
            "flag": True,
            "count": 3,
            "roles": {
                "code-reviewer": {
                    "tier": "powerful",
                    "description": "Gatekeeper:colon, dash — unicode ✓",
                    "keywords": ["Code Review", "Code-Qualität"],
                    "input_contracts": ["dev-result-v1"],
                    "output_contract": None,
                },
            },
        }
        rendered = hermes_export._emit_yaml(data) + "\n"
        assert yaml.safe_load(rendered) == data

    def test_sequence_items_share_key_indent(self) -> None:
        rendered = hermes_export._emit_yaml({"keywords": ["a", "b"]})
        assert rendered.splitlines() == ['keywords:', '- "a"', '- "b"']

    def test_nested_collection_in_sequence_rejected(self) -> None:
        with pytest.raises(TypeError, match="Nested collections"):
            hermes_export._emit_yaml({"rows": [["a"]]})


# ===========================================================================
# Abstract tier resolution (model-ID leak guard)
# ===========================================================================

class TestResolveAbstractTier:
    @pytest.mark.parametrize("tier", list(hermes_export.EXPORT_TIERS))
    def test_abstract_tiers_pass_through(self, tier: str) -> None:
        resolved, warning = hermes_export.resolve_abstract_tier(tier)
        assert resolved == tier
        assert warning is None

    @pytest.mark.parametrize(
        ("alias", "expected"),
        [("haiku", "fast"), ("sonnet", "balanced"), ("opus", "powerful")],
    )
    def test_legacy_claude_aliases(self, alias: str, expected: str) -> None:
        resolved, warning = hermes_export.resolve_abstract_tier(alias)
        assert resolved == expected
        assert warning is None

    def test_ultra_collapses_to_max_with_warning(self) -> None:
        resolved, warning = hermes_export.resolve_abstract_tier("ultra")
        assert resolved == "max"
        assert warning is not None and "ultra" in warning

    def test_empty_value_defaults_with_warning(self) -> None:
        resolved, warning = hermes_export.resolve_abstract_tier("")
        assert resolved == "balanced"
        assert warning is not None and "no abstract tier" in warning

    @pytest.mark.parametrize(
        "model_id",
        ["claude-sonnet-4-6", "opencode-go/kimi-k2.6", "gpt-5.4", "nonsense"],
    )
    def test_model_ids_never_leak(self, model_id: str) -> None:
        resolved, warning = hermes_export.resolve_abstract_tier(model_id)
        assert resolved in hermes_export.EXPORT_TIERS
        assert warning is not None and "model ID" in warning

    def test_result_always_in_export_vocabulary(self) -> None:
        for value in ("", "ultra", "sonnet", "claude-opus-4-8", "max", "max"):
            resolved, _ = hermes_export.resolve_abstract_tier(value)
            assert resolved in hermes_export.EXPORT_TIERS


# ===========================================================================
# export_skill_pack against the synthetic mini root
# ===========================================================================

class TestExportSkillPackMiniRepo:
    def test_writes_expected_layout(self, mini_meta: Path, tmp_path: Path) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out)
        assert summary["dry_run"] is False
        assert summary["written"] == [
            "roles/alpha/SKILL.md",
            "roles/alpha/references/persona.md",
            "roles/gamma/SKILL.md",
            "roles/gamma/references/persona.md",
            "manifest.yaml",
        ]
        assert (out / "manifest.yaml").is_file()
        assert (out / "roles" / "alpha" / "SKILL.md").is_file()
        assert (out / "roles" / "alpha" / "references" / "persona.md").is_file()

    def test_excludes_deprecated_and_reserved(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        summary = hermes_export.export_skill_pack(mini_meta, tmp_path / "pack")
        assert list(summary["roles"]) == ["alpha", "gamma"]
        assert not (tmp_path / "pack" / "roles" / "beta").exists()
        assert not (tmp_path / "pack" / "roles" / "_reserved").exists()

    def test_skill_md_frontmatter_is_valid_and_complete(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        hermes_export.export_skill_pack(mini_meta, out)
        text = (out / "roles" / "alpha" / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        fm = yaml.safe_load(text.split("\n---\n", 1)[0].removeprefix("---\n"))
        assert fm["name"] == "agent-meta-alpha"
        assert "Alpha role description." in fm["description"]
        assert "Triggers: Alpha, Test." in fm["description"]
        assert fm["version"] == "9.9.9-test"
        assert fm["metadata"]["agent-meta"]["role"] == "alpha"
        assert fm["metadata"]["agent-meta"]["tier"] == "fast"
        assert fm["metadata"]["agent-meta"]["source"] == "agents/1-generic/alpha.md"
        # Body: persona reference + structured-response instruction.
        assert "references/persona.md" in text
        assert "STATUS" in text and "ARTIFACTS" in text

    def test_manifest_structure(self, mini_meta: Path, tmp_path: Path) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out)
        manifest = yaml.safe_load(summary["manifest"])
        assert manifest["agent-meta-version"] == "9.9.9-test"
        assert manifest["format"] == "hermes-skillpack"
        assert manifest["format-version"] == "0.1.0"
        assert "NO model IDs" in manifest["note"]
        assert manifest["tier-order"] == [
            "nano", "fast", "balanced", "powerful", "max",
        ]
        entry = manifest["roles"]["alpha"]
        assert entry["tier"] == "fast"
        assert entry["description"] == "Alpha role description."
        assert entry["keywords"] == ["Alpha", "Test"]
        assert entry["output_contract"] == "dev-result-v1"
        assert entry["input_contracts"] == ["task-spec-v1"]
        assert entry["input_schema"] == "schemas/handoffs/task-spec.schema.json"
        assert entry["output_schema"] is None
        assert entry["skill"] == "roles/alpha/SKILL.md"
        assert entry["persona"] == "roles/alpha/references/persona.md"

    def test_manifest_paths_point_to_written_files(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out)
        manifest = yaml.safe_load(summary["manifest"])
        for entry in manifest["roles"].values():
            assert (out / entry["skill"]).is_file()
            assert (out / entry["persona"]).is_file()

    def test_written_manifest_file_matches_summary(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out)
        on_disk = (out / "manifest.yaml").read_text(encoding="utf-8")
        assert on_disk == summary["manifest"]

    def test_no_model_ids_anywhere_in_pack(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        hermes_export.export_skill_pack(mini_meta, out)
        assert _scan_model_ids(out) == []

    def test_orphan_role_defaults_to_balanced_with_warning(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        # gamma has no role-defaults entry -> empty model value -> balanced.
        summary = hermes_export.export_skill_pack(mini_meta, tmp_path / "pack")
        assert summary["roles"]["gamma"]["tier"] == "balanced"
        assert any(
            w.startswith("gamma: no abstract tier") for w in summary["warnings"]
        )

    def test_model_id_in_role_defaults_falls_back_with_warning(
        self, tmp_path: Path
    ) -> None:
        # A raw model ID in role-defaults.yaml must never surface in the
        # export — it falls back to the default tier with a warning.
        # Own root (fresh tmp_path): role-defaults loaders are process-
        # lifetime cached per root (#553).
        root = _make_mini_meta(tmp_path, alpha_model="claude-sonnet-4-6")
        summary = hermes_export.export_skill_pack(root, tmp_path / "pack")
        assert summary["roles"]["alpha"]["tier"] == "balanced"
        assert any("claude-sonnet-4-6" in w for w in summary["warnings"])
        assert "claude-sonnet-4-6" not in summary["manifest"]
        assert _scan_model_ids(tmp_path / "pack") == []

    def test_frontmatter_description_fallback_for_orphan_template(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        # gamma has no role-defaults entry: description falls back to the
        # template frontmatter (provider-expert situation).
        summary = hermes_export.export_skill_pack(mini_meta, tmp_path / "pack")
        assert summary["roles"]["gamma"]["description"] == (
            "Gamma standalone description."
        )

    def test_dry_run_writes_nothing(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out, dry_run=True)
        assert summary["dry_run"] is True
        assert summary["written"]  # would-be paths are still reported
        assert summary["manifest"]  # manifest is still computed
        assert not out.exists()

    def test_roles_filter_and_skip_reasons(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        summary = hermes_export.export_skill_pack(
            mini_meta, tmp_path / "pack", roles=["alpha", "beta", "ghost"]
        )
        assert list(summary["roles"]) == ["alpha"]
        skipped = dict(summary["skipped"])
        assert skipped["beta"] == "template is deprecated: true"
        assert skipped["ghost"] == "no template in agents/1-generic/"

    def test_roles_filter_deduplicates(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        summary = hermes_export.export_skill_pack(
            mini_meta, tmp_path / "pack", roles=["alpha", "alpha", "gamma"]
        )
        assert list(summary["roles"]) == ["alpha", "gamma"]

    def test_tier_override_applied(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        summary = hermes_export.export_skill_pack(
            mini_meta, tmp_path / "pack", tier_overrides={"alpha": "max"}
        )
        assert summary["roles"]["alpha"]["tier"] == "max"
        skill_text = (tmp_path / "pack" / "roles" / "alpha" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert 'tier: "max"' in skill_text

    def test_tier_override_rejects_model_id(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        with pytest.raises(ValueError, match="only abstract tiers"):
            hermes_export.export_skill_pack(
                mini_meta,
                tmp_path / "pack",
                tier_overrides={"alpha": "claude-opus-4-8"},
            )

    def test_tier_override_for_unknown_role_is_ignored(
        self, mini_meta: Path, tmp_path: Path
    ) -> None:
        summary = hermes_export.export_skill_pack(
            mini_meta, tmp_path / "pack", tier_overrides={"ghost": "nano"}
        )
        assert "ghost" not in summary["roles"]
        assert summary["roles"]["alpha"]["tier"] == "fast"

    def test_export_is_idempotent(self, mini_meta: Path, tmp_path: Path) -> None:
        out = tmp_path / "pack"
        hermes_export.export_skill_pack(mini_meta, out)
        first = {
            p.relative_to(out): p.read_bytes() for p in sorted(out.rglob("*"))
            if p.is_file()
        }
        hermes_export.export_skill_pack(mini_meta, out)
        second = {
            p.relative_to(out): p.read_bytes() for p in sorted(out.rglob("*"))
            if p.is_file()
        }
        assert first == second

    def test_refuses_source_tree_output(self, mini_meta: Path) -> None:
        with pytest.raises(ValueError, match="source tree"):
            hermes_export.export_skill_pack(mini_meta, mini_meta)

    def test_invalid_root_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="agents/1-generic"):
            hermes_export.export_skill_pack(tmp_path / "nope", tmp_path / "pack")


# ===========================================================================
# Export config loading
# ===========================================================================

class TestLoadExportConfig:
    def test_json_config_roundtrip(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text(
            json.dumps({"roles": ["alpha", "gamma"], "tiers": {"alpha": "nano"}}),
            encoding="utf-8",
        )
        roles, tiers = hermes_export._load_export_config(cfg)
        assert roles == ["alpha", "gamma"]
        assert tiers == {"alpha": "nano"}

    @pytest.mark.skipif(
        not hermes_export._YAML_AVAILABLE, reason="PyYAML not installed"
    )
    def test_yaml_config_roundtrip(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.yaml"
        cfg.write_text(
            "roles: [alpha, gamma]\ntiers:\n  alpha: balanced\n",
            encoding="utf-8",
        )
        roles, tiers = hermes_export._load_export_config(cfg)
        assert roles == ["alpha", "gamma"]
        assert tiers == {"alpha": "balanced"}

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Export config not found"):
            hermes_export._load_export_config(tmp_path / "missing.yaml")

    def test_unsupported_suffix_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.toml"
        cfg.write_text("roles = []\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported export-config suffix"):
            hermes_export._load_export_config(cfg)

    def test_non_mapping_top_level_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text("[]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="expected a mapping"):
            hermes_export._load_export_config(cfg)

    def test_non_mapping_tiers_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text('{"tiers": ["nano"]}\n', encoding="utf-8")
        with pytest.raises(ValueError, match="'tiers' must be a mapping"):
            hermes_export._load_export_config(cfg)

    def test_unknown_keys_warn_but_do_not_fail(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text('{"roles": ["alpha"], "tier": {"alpha": "max"}}\n', encoding="utf-8")
        roles, tiers = hermes_export._load_export_config(cfg)
        assert roles == ["alpha"]
        assert tiers == {}
        stderr = capsys.readouterr().err
        assert "unknown key(s): tier" in stderr

    def test_invalid_json_raises_value_error(self, tmp_path: Path) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            hermes_export._load_export_config(cfg)


# ===========================================================================
# CLI wiring
# ===========================================================================

class TestCli:
    def _run_main(self, monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> int:
        monkeypatch.setattr(sys, "argv", ["hermes_export.py", *argv])
        return hermes_export.main()

    def test_main_real_run(
        self, monkeypatch: pytest.MonkeyPatch, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        code = self._run_main(
            monkeypatch,
            ["--root", str(mini_meta), "--output", str(out), "--roles", "alpha"],
        )
        assert code == 0
        assert (out / "manifest.yaml").is_file()
        assert (out / "roles" / "alpha" / "SKILL.md").is_file()

    def test_main_dry_run_writes_nothing(
        self, monkeypatch: pytest.MonkeyPatch, mini_meta: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        code = self._run_main(
            monkeypatch,
            ["--root", str(mini_meta), "--output", str(out), "--dry-run"],
        )
        assert code == 0
        assert not out.exists()

    def test_main_invalid_tier_override_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, mini_meta: Path, tmp_path: Path
    ) -> None:
        cfg = tmp_path / "curation.json"
        cfg.write_text('{"tiers": {"alpha": "gpt-5.4"}}\n', encoding="utf-8")
        code = self._run_main(
            monkeypatch,
            [
                "--root", str(mini_meta),
                "--output", str(tmp_path / "pack"),
                "--export-config", str(cfg),
            ],
        )
        assert code == 1

    def test_main_missing_export_config_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, mini_meta: Path, tmp_path: Path
    ) -> None:
        code = self._run_main(
            monkeypatch,
            [
                "--root", str(mini_meta),
                "--output", str(tmp_path / "pack"),
                "--export-config", str(tmp_path / "missing.yaml"),
            ],
        )
        assert code == 1

    def test_main_invalid_root_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        code = self._run_main(
            monkeypatch,
            ["--root", str(tmp_path / "void"), "--output", str(tmp_path / "pack")],
        )
        assert code == 1


# ===========================================================================
# Integration smoke against the real agent-meta repo
# ===========================================================================

class TestRealRepoIntegration:
    @pytest.fixture()
    def real_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def test_export_two_roles_real_repo(
        self, real_root: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(
            real_root, out, roles=["developer", "orchestrator"]
        )
        assert list(summary["roles"]) == ["developer", "orchestrator"]

        manifest = yaml.safe_load(summary["manifest"])
        roles_cfg = hermes_export.load_roles_config(real_root)["roles"]
        for role in ("developer", "orchestrator"):
            entry = manifest["roles"][role]
            # Tier must be the abstract tier from role-defaults (dynamic
            # expectation — role-defaults stays the single source of truth).
            expected, _ = hermes_export.resolve_abstract_tier(
                str(roles_cfg[role].get("model", ""))
            )
            assert entry["tier"] == expected
            assert entry["skill"] == f"roles/{role}/SKILL.md"
            skill_text = (out / entry["skill"]).read_text(encoding="utf-8")
            fm = yaml.safe_load(
                skill_text.split("\n---\n", 1)[0].removeprefix("---\n")
            )
            assert fm["name"] == f"agent-meta-{role}"
            assert fm["description"]
            assert fm["version"]
            persona = (out / entry["persona"]).read_text(encoding="utf-8")
            assert persona.strip()
            # Rendered persona must not leak raw placeholders.
            assert not re.search(r"\{\{[A-Z0-9_]+\}\}", persona)

        # Manifest + skill frontmatter carry no model IDs (persona prose is
        # excluded — see module docstring note).
        assert _MODEL_ID_RE.search(summary["manifest"]) is None
        for role in ("developer", "orchestrator"):
            skill_text = (out / "roles" / role / "SKILL.md").read_text(
                encoding="utf-8"
            )
            assert _MODEL_ID_RE.search(skill_text) is None
