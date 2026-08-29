"""Unit tests for ``scripts/admin-server.py``.

The admin-server module is loaded via :mod:`importlib` because the file name
contains a hyphen (``admin-server.py``) which prevents the usual
``import scripts.admin_server`` syntax. The module is loaded once at module
import time and shared across test cases.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import yaml

# --------------------------------------------------------------------------- #
# Module loading                                                              #
# --------------------------------------------------------------------------- #

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _PROJECT_ROOT / "scripts" / "admin-server.py"
# `lib.agents` (used by `_template_path`) is imported lazily, at call time, from
# whatever `<test-root>/scripts` happens to be — tests that exercise it against
# a throwaway temp root (which has no scripts/lib of its own) need the REAL
# scripts/lib importable up front, not resolved through the fake root.
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


def _load_admin_server():
    """Load ``admin-server.py`` as a Python module."""
    spec = importlib.util.spec_from_file_location("admin_server", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


# --------------------------------------------------------------------------- #
# Mode detection                                                              #
# --------------------------------------------------------------------------- #


class TestDetectMode(unittest.TestCase):
    def test_super_admin_when_generic_agents_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents" / "1-generic").mkdir(parents=True)
            self.assertEqual(admin_server.detect_mode(root), "super_admin")

    def test_project_admin_when_generic_agents_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # No agents/1-generic dir
            self.assertEqual(admin_server.detect_mode(root), "project_admin")

    def test_project_admin_when_only_submodule_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".agent-meta").mkdir()
            self.assertEqual(admin_server.detect_mode(root), "project_admin")


# --------------------------------------------------------------------------- #
# ConfigManager                                                               #
# --------------------------------------------------------------------------- #


class TestConfigManagerRead(unittest.TestCase):
    def test_read_roundtrip_preserves_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir()
            payload = {"name": "demo", "nested": {"key": [1, 2, 3], "flag": True}}
            mgr = admin_server.ConfigManager(root, mode="project_admin")
            mgr.write("project", payload)
            result = mgr.read("project")
            self.assertEqual(result, payload)

    def test_read_missing_file_returns_empty_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="project_admin")
            self.assertEqual(mgr.read("project"), {})


class TestBackupCreation(unittest.TestCase):
    def test_write_creates_backup_with_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir()
            mgr = admin_server.ConfigManager(root, mode="project_admin")
            mgr.write("project", {"version": 1})
            # Second write must produce a backup of the first one
            mgr.write("project", {"version": 2})
            backups = list((root / ".meta-config").glob("project.yaml.bak.*"))
            self.assertGreaterEqual(len(backups), 1)
            # Backup contains the *previous* contents
            backup_text = backups[0].read_text(encoding="utf-8")
            self.assertIn("version: 1", backup_text)

    def test_backup_pruning_keeps_at_most_max_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir()
            mgr = admin_server.ConfigManager(root, mode="project_admin")
            # Perform MAX_BACKUPS + 3 writes to force pruning
            for i in range(admin_server.MAX_BACKUPS + 3):
                mgr.write("project", {"version": i})
            backups = list((root / ".meta-config").glob("project.yaml.bak.*"))
            self.assertLessEqual(len(backups), admin_server.MAX_BACKUPS)


# --------------------------------------------------------------------------- #
# Security checks                                                             #
# --------------------------------------------------------------------------- #


class TestWritePathWhitelist(unittest.TestCase):
    def test_unknown_key_raises_security_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="project_admin")
            with self.assertRaises(admin_server.SecurityError):
                mgr.write("definitely-not-allowed", {"x": 1})

    def test_super_admin_only_key_readable_in_project_mode(self) -> None:
        # resolve_path() (and by extension read()) is deliberately
        # mode-agnostic -- project_admin mode must still be able to *view*
        # framework defaults like role-defaults.yaml. The actual write
        # boundary is enforced in write(), tested below. This test used to
        # assert the opposite (a stale expectation that predates that design
        # decision) and had been failing for weeks without anyone checking
        # whether it pointed at a real vulnerability -- it didn't; write()
        # already rejects this key in project_admin mode (audit follow-up,
        # 2026-08-07).
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="project_admin")
            path = mgr.resolve_path("role-defaults")
            self.assertTrue(str(path).endswith("role-defaults.yaml"))

    def test_super_admin_only_key_rejected_on_write_in_project_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="project_admin")
            with self.assertRaises(admin_server.SecurityError):
                mgr.write("role-defaults", {"roles": {}})

    def test_super_admin_key_allowed_in_super_admin_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="super_admin")
            path = mgr.resolve_path("role-defaults")
            self.assertTrue(str(path).endswith("role-defaults.yaml"))


class TestPathTraversalPrevention(unittest.TestCase):
    def test_traversal_segments_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="super_admin")
            for bad in ("../../etc/passwd", "..\\windows\\system32", "/etc/shadow",
                        "config/../../../secrets.yaml"):
                with self.assertRaises(admin_server.SecurityError, msg=f"key={bad!r} should be rejected"):
                    mgr.resolve_path(bad)

    def test_empty_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mgr = admin_server.ConfigManager(Path(tmp), mode="super_admin")
            with self.assertRaises(admin_server.SecurityError):
                mgr.resolve_path("")


class TestTemplatePathSecurity(unittest.TestCase):
    """``_template_path`` is the only place that maps user-controlled role
    names to filesystem paths for agent templates; it must reject every form
    of traversal/injection."""

    def _make_handler(self, root: Path):
        """Build a bare handler instance without actually serving a request."""
        handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
        admin_server.AdminRequestHandler.root = root
        return handler

    def test_rejects_empty_role_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = self._make_handler(Path(tmp))
            with self.assertRaises(admin_server.SecurityError):
                handler._template_path("")

    def test_rejects_traversal_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = self._make_handler(Path(tmp))
            for bad in ("..", "../foo", "..\\bar", "foo/bar", "foo\\bar",
                        "../../etc/passwd"):
                with self.assertRaises(admin_server.SecurityError,
                                       msg=f"role={bad!r} should be rejected"):
                    handler._template_path(bad)

    def test_rejects_slash_only_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = self._make_handler(Path(tmp))
            for bad in ("/", "\\", "/etc"):
                with self.assertRaises(admin_server.SecurityError,
                                       msg=f"role={bad!r} should be rejected"):
                    handler._template_path(bad)

    def test_rejects_special_characters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = self._make_handler(Path(tmp))
            # Any character that is not alnum / dash / underscore is forbidden.
            for bad in ("foo bar", "foo.bar", "foo$bar", "foo;bar", "foo`bar"):
                with self.assertRaises(admin_server.SecurityError,
                                       msg=f"role={bad!r} should be rejected"):
                    handler._template_path(bad)

    def test_accepts_well_formed_role_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = self._make_handler(Path(tmp))
            path = handler._template_path("code-reviewer")
            self.assertTrue(str(path).endswith(os.path.join("1-generic", "code-reviewer.md")))

    def test_resolves_override_only_from_active_platform(self) -> None:
        """A role with SEVERAL same-named 2-platform overrides must resolve
        to the one belonging to THIS project's active platform — not
        whichever file glob() happens to list first. Regression test for a
        bug where `_template_path` globbed agents/2-platform/*.md across
        every platform on disk, so Save could silently overwrite an
        unrelated, inactive platform's agent file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generic = root / "agents" / "1-generic"
            platform = root / "agents" / "2-platform"
            generic.mkdir(parents=True)
            platform.mkdir(parents=True)
            (generic / "developer.md").write_text("---\nname: developer\n---\ngeneric body", encoding="utf-8")
            # Two platforms both override "developer" — only "agent-meta" is
            # active for this project; "sharkord"'s override must be ignored.
            (platform / "sharkord-developer.md").write_text("---\nname: developer\n---\nsharkord body", encoding="utf-8")
            (platform / "agent-meta-developer.md").write_text("---\nname: developer\n---\nagent-meta body", encoding="utf-8")

            handler = self._make_handler(root)
            admin_server.AdminRequestHandler.config_manager = mock.Mock(
                read=mock.Mock(return_value={"platforms": ["agent-meta"]})
            )
            try:
                path = handler._template_path("developer")
            finally:
                del admin_server.AdminRequestHandler.config_manager
            self.assertEqual(path.name, "agent-meta-developer.md")

    def test_falls_back_to_generic_when_no_platform_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generic = root / "agents" / "1-generic"
            platform = root / "agents" / "2-platform"
            generic.mkdir(parents=True)
            platform.mkdir(parents=True)
            (generic / "developer.md").write_text("---\nname: developer\n---\ngeneric body", encoding="utf-8")
            (platform / "sharkord-developer.md").write_text("---\nname: developer\n---\nsharkord body", encoding="utf-8")

            handler = self._make_handler(root)
            admin_server.AdminRequestHandler.config_manager = mock.Mock(
                read=mock.Mock(return_value={"platforms": []})
            )
            try:
                path = handler._template_path("developer")
            finally:
                del admin_server.AdminRequestHandler.config_manager
            self.assertTrue(str(path).endswith(os.path.join("1-generic", "developer.md")))


# --------------------------------------------------------------------------- #
# Pricing overlay merge                                                       #
# --------------------------------------------------------------------------- #


class TestApplyPricingOverlay(unittest.TestCase):
    """config/pricing-overlay.yaml key formats are inconsistent across
    providers: most use bare model ids matching models.dev directly, but
    opencode-go's ids are prefixed with "opencode-go/" (that prefix is the
    real, runnable model id for this framework's `model:` field). Regression
    coverage for the resulting id-format mismatch in the live models.dev
    merge path."""

    def _make_handler(self, root: Path, pricing_yaml: str):
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "config" / "pricing-overlay.yaml").write_text(pricing_yaml, encoding="utf-8")
        handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
        admin_server.AdminRequestHandler.root = root
        return handler

    def test_prefixed_overlay_key_matches_bare_models_dev_id(self) -> None:
        pricing_yaml = (
            "prices:\n"
            "  opencode-go:\n"
            "    opencode-go/minimax-m3:\n"
            "      input: 0.0\n"
            "      output: 0.0\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root, pricing_yaml)
            providers = {
                "opencode-go": {
                    "name": "OpenCode Go",
                    "models": {
                        # models.dev's own live catalog uses the bare id —
                        # no "opencode-go/" prefix.
                        "minimax-m3": {"id": "minimax-m3", "cost": {"input": 5.0, "output": 15.0}},
                    },
                },
            }
            merged = handler._apply_pricing_overlay(providers)
            models = merged["opencode-go"]["models"]
            # Patched in place under the bare id — no duplicate prefixed key.
            self.assertEqual(set(models.keys()), {"minimax-m3"})
            self.assertEqual(models["minimax-m3"]["cost"], {"input": 0.0, "output": 0.0})
            self.assertEqual(models["minimax-m3"]["_costSource"], "overlay")

    def test_bare_overlay_key_still_matches_bare_models_dev_id(self) -> None:
        """Non-prefixed providers (anthropic, gemini, ...) must keep working
        exactly as before — this is not opencode-go-specific behavior."""
        pricing_yaml = (
            "prices:\n"
            "  anthropic:\n"
            "    claude-sonnet-4-6:\n"
            "      input: 3.0\n"
            "      output: 15.0\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root, pricing_yaml)
            providers = {
                "anthropic": {
                    "name": "Anthropic",
                    "models": {
                        "claude-sonnet-4-6": {"id": "claude-sonnet-4-6", "cost": {"input": 99.0, "output": 99.0}},
                    },
                },
            }
            merged = handler._apply_pricing_overlay(providers)
            model = merged["anthropic"]["models"]["claude-sonnet-4-6"]
            self.assertEqual(model["cost"], {"input": 3.0, "output": 15.0})
            self.assertEqual(model["_costSource"], "overlay")

    def test_overlay_key_matching_neither_form_is_ignored(self) -> None:
        pricing_yaml = (
            "prices:\n"
            "  opencode-go:\n"
            "    opencode-go/nonexistent-model:\n"
            "      input: 1.0\n"
            "      output: 2.0\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root, pricing_yaml)
            providers = {
                "opencode-go": {
                    "name": "OpenCode Go",
                    "models": {
                        "minimax-m3": {"id": "minimax-m3", "cost": {"input": 5.0, "output": 15.0}},
                    },
                },
            }
            merged = handler._apply_pricing_overlay(providers)
            models = merged["opencode-go"]["models"]
            self.assertEqual(set(models.keys()), {"minimax-m3"})
            self.assertNotIn("_costSource", models["minimax-m3"])
            self.assertEqual(models["minimax-m3"]["cost"], {"input": 5.0, "output": 15.0})


# --------------------------------------------------------------------------- #
# Atomic-write cleanup                                                        #
# --------------------------------------------------------------------------- #


class TestAtomicWriteCleanup(unittest.TestCase):
    """The atomic-write contract: on yaml.dump failure the .tmp file must
    NOT be left behind in the config directory."""

    def test_tmp_file_removed_when_yaml_dump_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir()
            mgr = admin_server.ConfigManager(root, mode="project_admin")

            # Force yaml.dump to fail mid-write.
            with mock.patch.object(admin_server.yaml, "dump",  # noqa: SIM117
                                   side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    mgr.write("project", {"x": 1})

            # No orphaned .tmp file should remain.
            leftover = list((root / ".meta-config").glob("*.tmp"))
            self.assertEqual(leftover, [],
                             msg=f"expected no .tmp leftovers, found {leftover}")

    def test_tmp_file_removed_when_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".meta-config").mkdir()
            mgr = admin_server.ConfigManager(root, mode="project_admin")

            with mock.patch.object(admin_server.os, "replace",  # noqa: SIM117
                                   side_effect=OSError("locked")):
                with self.assertRaises(OSError):
                    mgr.write("project", {"x": 1})

            leftover = list((root / ".meta-config").glob("*.tmp"))
            self.assertEqual(leftover, [],
                             msg=f"expected no .tmp leftovers, found {leftover}")


# --------------------------------------------------------------------------- #
# Bind-host enforcement                                                       #
# --------------------------------------------------------------------------- #


class TestBindHostEnforcement(unittest.TestCase):
    """The admin server must refuse to bind on anything other than loopback."""

    def test_non_loopback_host_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents" / "1-generic").mkdir(parents=True)
            for bad_host in ("0.0.0.0", "192.168.0.1", "example.com", "::"):
                with self.assertRaises(ValueError, msg=f"host={bad_host!r} should be rejected"):
                    admin_server.AdminServer(root, host=bad_host, port=0)

    def test_loopback_host_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "agents" / "1-generic").mkdir(parents=True)
            with mock.patch.object(admin_server, "_DaemonThreadingHTTPServer") as srv_cls:
                srv_cls.return_value = mock.Mock()
                # Should not raise for any allowed host.
                for ok_host in admin_server.DEFAULT_ALLOWED_HOSTS:
                    admin_server.AdminServer(root, host=ok_host, port=0)


# --------------------------------------------------------------------------- #
# SyncExecutor                                                                #
# --------------------------------------------------------------------------- #


class TestSyncExecutorDryRun(unittest.TestCase):
    def test_dry_run_invokes_subprocess_with_validate_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "sync.py").write_text("# stub", encoding="utf-8")

            executor = admin_server.SyncExecutor(root)
            fake_result = mock.Mock(returncode=0, stdout="OK", stderr="")
            with mock.patch.object(admin_server.subprocess, "run", return_value=fake_result) as run_mock:
                result = executor.dry_run()
            self.assertTrue(result["success"])
            self.assertIn("OK", result["output"])
            # Verify --validate was passed
            args = run_mock.call_args[0][0]
            self.assertIn("--validate", args)

    def test_missing_sync_script_reports_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor = admin_server.SyncExecutor(Path(tmp))
            result = executor.dry_run()
            self.assertFalse(result["success"])
            self.assertIn("sync.py not found", result["output"])


# --------------------------------------------------------------------------- #
# Server bootstrap (no socket binding)                                        #
# --------------------------------------------------------------------------- #


class TestAdminServerVersion(unittest.TestCase):
    def test_version_read_from_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "agents" / "1-generic").mkdir(parents=True)
            # Use a high random-ish port that will not bind; patch the
            # daemon-threading subclass used by AdminServer.
            with mock.patch.object(admin_server, "_DaemonThreadingHTTPServer") as srv_cls:
                srv_cls.return_value = mock.Mock()
                server = admin_server.AdminServer(root, host="127.0.0.1", port=0)
            self.assertEqual(server.mode, "super_admin")
            self.assertEqual(admin_server.AdminRequestHandler.version, "1.2.3")


# --------------------------------------------------------------------------- #
# Submodule-protection save/restore                                           #
# --------------------------------------------------------------------------- #


class TestWriteSubmoduleProtection(unittest.TestCase):
    """The save path must not leave a stale nested ``rules.submodule-protection``
    key behind once the flat key has been written (config-drift regression)."""

    def _make_handler(self, root: Path, body: dict) -> Any:
        """Build a bare handler instance with a real ``ConfigManager`` and a
        stubbed request body, without spinning up an actual HTTP connection."""
        (root / ".meta-config").mkdir(parents=True, exist_ok=True)
        handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
        admin_server.AdminRequestHandler.root = root
        admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
            root, mode="project_admin"
        )
        handler._read_body = mock.Mock(return_value=body)  # type: ignore[method-assign]
        handler._send_json = mock.Mock()  # type: ignore[method-assign]
        return handler

    def test_save_removes_stale_nested_rules_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root, {
                "restore_default": False,
                "enabled": True,
                "override_text": "new override text",
            })
            # Seed a pre-existing stale nested override, as left over from an
            # older save path that predates this fix.
            admin_server.AdminRequestHandler.config_manager.write(
                "project", {"rules": {"submodule-protection": "old nested override text"}}
            )

            handler._write_submodule_protection()

            saved = admin_server.AdminRequestHandler.config_manager.read("project")
            self.assertEqual(saved.get("submodule-protection"), "new override text")
            self.assertNotIn("submodule-protection", saved.get("rules", {}))


# --------------------------------------------------------------------------- #
# Injection-drift endpoint — submodule (project_admin) root resolution        #
# --------------------------------------------------------------------------- #


class TestComputeInjectionDrift(unittest.TestCase):
    """_compute_injection_drift() must resolve the framework registries via
    ``self._agent_meta_root()``, not the raw project root — in project_admin
    (submodule) mode those live under ``.agent-meta/``, not the project root
    itself (config-drift regression: passing the wrong root silently falls
    back to a stub provider config and produces false-positive findings)."""

    def _make_handler(self, root: Path) -> Any:
        handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
        admin_server.AdminRequestHandler.root = root
        admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
            root, mode="project_admin"
        )
        return handler

    def test_uses_agent_meta_root_not_project_root_for_provider_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submodule = root / ".agent-meta"
            # Marks this as project_admin mode for detect_mode()/_agent_meta_root().
            (submodule / "agents" / "1-generic").mkdir(parents=True)
            (submodule / "config").mkdir(parents=True)
            # scripts/lib is imported by _compute_injection_drift() itself — point
            # it at the real repo's lib package rather than re-vendoring it into
            # the fixture, so this test exercises the actual scan_injection_drift.
            (submodule / "scripts").symlink_to(_PROJECT_ROOT / "scripts")
            (submodule / "config" / "ai-providers.yaml").write_text(
                "providers:\n"
                "  ZzzTestProvider:\n"
                "    agents_dir: .zzz/agents\n"
                "    has_hooks: false\n"
                "    has_rules: false\n"
                "    capabilities: []\n",
                encoding="utf-8",
            )
            (root / ".meta-config").mkdir(parents=True)
            (root / ".meta-config" / "project.yaml").write_text("ai-providers: []\n", encoding="utf-8")

            handler = self._make_handler(root)
            result = handler._compute_injection_drift()

            self.assertNotIn("error", result, result.get("error"))
            # "ZzzTestProvider" only exists in .agent-meta/config/ai-providers.yaml
            # — its presence proves load_providers_config() was called with the
            # submodule root. The old bug passed the (empty) project root instead,
            # silently falling back to a Claude-only stub and never seeing this
            # provider at all.
            self.assertIn("ZzzTestProvider", result["findings"])


# --------------------------------------------------------------------------- #
# Model suggestions — registry id convention (opencode-go prefix)             #
# --------------------------------------------------------------------------- #


_MODELS_DEV_CACHE_ATTRS = (
    "_models_dev_cache",
    "_models_dev_cache_ts",
    "_models_dev_error",
    "_models_dev_last_fetch_error",
)


def _reset_models_dev_class_state() -> None:
    """Clear the class-level models.dev cache attributes so tests start from
    a cold cache and cannot leak state into each other."""
    for attr in _MODELS_DEV_CACHE_ATTRS:
        if hasattr(admin_server.AdminRequestHandler, attr):
            delattr(admin_server.AdminRequestHandler, attr)


def _make_models_handler(root: Path,
                         registry_models: list[dict],
                         ai_providers: dict | None = None,
                         project: dict | None = None,
                         pricing_yaml: str | None = None):
    """Build a bare AdminRequestHandler wired to a super-admin fixture root.

    Creates ``config/generated/model-registry.json`` (and optionally
    ``config/ai-providers.yaml``, ``.meta-config/project.yaml`` and
    ``config/pricing-overlay.yaml``) so the suggestion/overlay/curation code
    paths run against controlled data instead of the real repository.
    """
    (root / "agents" / "1-generic").mkdir(parents=True, exist_ok=True)
    config_dir = root / "config"
    generated = config_dir / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "model-registry.json").write_text(
        json.dumps({"models": registry_models}), encoding="utf-8")
    if ai_providers is not None:
        (config_dir / "ai-providers.yaml").write_text(
            yaml.dump(ai_providers, sort_keys=False), encoding="utf-8")
    if pricing_yaml is not None:
        (config_dir / "pricing-overlay.yaml").write_text(pricing_yaml, encoding="utf-8")
    if project is not None:
        (root / ".meta-config").mkdir(exist_ok=True)
        (root / ".meta-config" / "project.yaml").write_text(
            yaml.dump(project, sort_keys=False), encoding="utf-8")

    handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="project_admin"
    )
    return handler


def _sample_registry_models() -> list[dict]:
    """Registry fixture mirroring the real id conventions: opencode-go ids
    are namespaced, anthropic ids are bare."""
    return [
        {"id": "opencode-go/glm-5", "name": "GLM 5", "provider": "opencode-go",
         "input_cost_api": 0.0, "output_cost_api": 0.0},
        {"id": "opencode-go/kimi-k3", "name": "Kimi K3", "provider": "opencode-go",
         "input_cost_api": 0.0, "output_cost_api": 0.0},
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic",
         "input_cost_api": 3.0, "output_cost_api": 15.0},
    ]


class TestSuggestionsModelsDevPrefix(unittest.TestCase):
    """models.dev-sourced suggestion ids must match the registry's id
    convention: sync persists tier values verbatim into the ``model:``
    frontmatter, so the namespaced ``opencode-go/<raw>`` ids must keep their
    prefix while bare-id providers (anthropic) stay 1:1 with models.dev."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    def _models_dev_payload(self) -> dict:
        return {
            "source": "api",
            "providers": {
                "opencode-go": {
                    "name": "OpenCode Go",
                    "models": {
                        "glm-5": {"id": "glm-5", "name": "GLM 5", "cost": {"input": 0.0, "output": 0.0}},
                        "kimi-k3": {"id": "kimi-k3", "name": "Kimi K3", "cost": {"input": 0.0, "output": 0.0}},
                    },
                },
                "anthropic": {
                    "name": "Anthropic",
                    "models": {
                        "claude-sonnet-4-6": {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6",
                                              "cost": {"input": 3.0, "output": 15.0}},
                    },
                },
            },
            "models": {},
        }

    def test_namespaced_provider_suggestions_carry_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, _sample_registry_models())
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value=self._models_dev_payload())

            models = handler._suggestions_from_models_dev("Opencode")
            self.assertEqual(
                [m["id"] for m in models],
                ["opencode-go/glm-5", "opencode-go/kimi-k3"],
            )

    def test_bare_provider_suggestions_stay_raw(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, _sample_registry_models())
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value=self._models_dev_payload())

            models = handler._suggestions_from_models_dev("Claude")
            self.assertEqual([m["id"] for m in models], ["claude-sonnet-4-6"])

    def test_prefix_convention_derived_from_registry_not_hardcoded(self) -> None:
        """A provider whose registry ids are ALL namespaced keeps prefixed
        suggestions even for models not yet in the registry — the convention
        is derived from the registry, never hardcoded."""
        registry = [
            {"id": "google/gemini-x", "name": "Gemini X", "provider": "google",
             "input_cost_api": 1.0, "output_cost_api": 2.0},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, registry)
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "source": "api",
                    "providers": {"google": {"name": "Google", "models": {
                        "gemini-x": {"id": "gemini-x", "name": "Gemini X",
                                     "cost": {"input": 1.0, "output": 2.0}},
                        "gemini-new": {"id": "gemini-new", "name": "Gemini New",
                                       "cost": {"input": 1.0, "output": 2.0}},
                    }}},
                    "models": {},
                })
            models = handler._suggestions_from_models_dev("Gemini")
            self.assertEqual(
                [m["id"] for m in models],
                ["google/gemini-x", "google/gemini-new"],
            )


class TestMixedConventionRegistryResolution(unittest.TestCase):
    """Registry id conventions are PER MODEL, not per provider: anthropic
    carries bare canonical ids AND namespaced OpenRouter extras, opencode-go
    namespaces everything. A provider-wide binary prefix heuristic produced
    non-runnable ``anthropic/...`` suggestions for canonical Claude models
    (this is exactly why the mixed shape must be in unit tests)."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    @staticmethod
    def _mixed_registry_models() -> list[dict]:
        return [
            # anthropic: MIXED conventions (13 bare canonical + 18 prefixed
            # OpenRouter extras in the real registry).
            {"id": "claude-opus-5", "name": "Claude Opus 5", "provider": "anthropic",
             "input_cost_api": 5.0, "output_cost_api": 25.0},
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic",
             "input_cost_api": 3.0, "output_cost_api": 15.0},
            {"id": "anthropic/claude-opus-4.8-fast", "name": "Claude Opus 4.8 Fast",
             "provider": "anthropic", "input_cost_api": 10.0, "output_cost_api": 50.0},
            {"id": "anthropic/claude-opus-5:batch", "name": "Claude Opus 5 Batch",
             "provider": "anthropic", "input_cost_api": 2.5, "output_cost_api": 12.5},
            # opencode-go: unanimously namespaced.
            {"id": "opencode-go/glm-5", "name": "GLM 5", "provider": "opencode-go",
             "input_cost_api": 0.0, "output_cost_api": 0.0},
            {"id": "opencode-go/kimi-k3", "name": "Kimi K3", "provider": "opencode-go",
             "input_cost_api": 0.0, "output_cost_api": 0.0},
        ]

    @staticmethod
    def _mixed_models_dev_payload() -> dict:
        return {
            "source": "api",
            "providers": {
                "anthropic": {
                    "name": "Anthropic",
                    "models": {
                        # canonical bare id that exists bare in the registry:
                        "claude-opus-5": {"id": "claude-opus-5", "name": "Claude Opus 5",
                                          "cost": {"input": 5.0, "output": 25.0}},
                        # not synced into the registry yet:
                        "claude-opus-9": {"id": "claude-opus-9", "name": "Claude Opus 9",
                                          "cost": {"input": 9.0, "output": 45.0}},
                    },
                },
                "opencode-go": {
                    "name": "OpenCode Go",
                    "models": {
                        # exists namespaced in the registry:
                        "glm-5": {"id": "glm-5", "name": "GLM 5",
                                  "cost": {"input": 0.0, "output": 0.0}},
                        # not synced into the registry yet:
                        "glm-5.3": {"id": "glm-5.3", "name": "GLM 5.3",
                                    "cost": {"input": 0.0, "output": 0.0}},
                    },
                },
            },
            "models": {},
        }

    def test_mixed_provider_resolves_per_model(self) -> None:
        """anthropic suggestions must stay bare (canonical, runnable);
        blanket provider-wide prefixing produced 'anthropic/claude-opus-5',
        which roles.py would persist verbatim into a broken model field."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, self._mixed_registry_models())
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value=self._mixed_models_dev_payload())

            models = handler._suggestions_from_models_dev("Claude")
            self.assertEqual(
                [m["id"] for m in models],
                ["claude-opus-5", "claude-opus-9"],
            )

    def test_unanimous_namespaced_provider_keeps_prefix_for_unsynced_models(self) -> None:
        """opencode-go models missing from the registry must STILL get the
        prefix (the unanimity fallback) — discovery namespaces every
        opencode-go id, so bare would be non-runnable once synced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, self._mixed_registry_models())
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value=self._mixed_models_dev_payload())

            models = handler._suggestions_from_models_dev("Opencode")
            self.assertEqual(
                [m["id"] for m in models],
                ["opencode-go/glm-5", "opencode-go/glm-5.3"],
            )

    def test_import_key_matches_collect_models_overlay_lookup(self) -> None:
        """End-to-end: an imported anthropic price must be written under the
        registry id _collect_models() looks up — with the old provider-wide
        rule it landed on 'anthropic/<bare>' and never surfaced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(
                root, self._mixed_registry_models(),
                pricing_yaml="prices:\n  anthropic: {}\n")
            handler._read_body = mock.Mock(return_value={  # type: ignore[method-assign]
                "provider": "anthropic", "model_id": "claude-opus-5",
                "input_cost": 7.0, "output_cost": 35.0,
            })
            captured: dict = {}
            handler._send_json = mock.Mock(  # type: ignore[method-assign]
                side_effect=lambda payload, status=200: captured.update({"payload": payload, "status": status}))

            handler._handle_post_models_dev_import()
            self.assertTrue(captured["payload"].get("success"), captured["payload"])
            self.assertEqual(captured["payload"]["model_id"], "claude-opus-5")

            # The imported price MUST now surface on the registry row.
            models = {m["id"]: m for m in handler._collect_models()}
            self.assertEqual(models["claude-opus-5"]["input_source"], "Overlay")
            self.assertEqual(models["claude-opus-5"]["input_cost"], 7.0)
            self.assertEqual(models["claude-opus-5"]["output_cost"], 35.0)


class TestSuggestionsDegradation(unittest.TestCase):
    """/api/model-suggestions must never serve a silently empty dropdown for
    a modelsdev-sourced provider when the models.dev catalog is unavailable,
    and the registry path must not degrade to a cross-provider soup."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    def _make_suggestions_handler(self, root: Path, provider: str = "Opencode") -> Any:
        ai_providers = {
            "providers": {
                "Opencode": {"model-tiers": {"balanced": "opencode-go/glm-5"}},
                "Gemini": {"model-tiers": {"balanced": "gemini-3.1-pro-low"}},
            },
        }
        project = {"model-source-preference": {"Opencode": "modelsdev"}}
        handler = _make_models_handler(root, _sample_registry_models(),
                                       ai_providers=ai_providers, project=project)
        handler.path = f"/api/model-suggestions?provider={provider}"
        captured: dict = {}
        handler._send_json = mock.Mock(  # type: ignore[method-assign]
            side_effect=lambda payload, status=200: captured.update({"payload": payload, "status": status}))
        return handler, captured

    def test_modelsdev_failure_degrades_to_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler, captured = self._make_suggestions_handler(root)
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value={"source": "error", "error": "models.dev fetch failed: boom",
                              "providers": {}, "models": {}})

            handler._handle_get_model_suggestions()

            payload = captured["payload"]
            self.assertEqual(payload["source"], "registry")
            ids = [m["id"] for m in payload["models"]]
            self.assertIn("opencode-go/glm-5", ids)
            # Degradation must be honest about the effective source, never
            # report "modelsdev" for registry-served rows.
            self.assertNotEqual(payload["source"], "modelsdev")

    def test_modelsdev_empty_node_degrades_to_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler, captured = self._make_suggestions_handler(root)
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value={"source": "api", "providers": {}, "models": {}})

            handler._handle_get_model_suggestions()

            payload = captured["payload"]
            self.assertEqual(payload["source"], "registry")
            self.assertTrue(payload["models"])

    def test_modelsdev_success_serves_prefixed_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler, captured = self._make_suggestions_handler(root)
            handler._load_models_dev_data = mock.Mock(  # type: ignore[method-assign]
                return_value={
                    "source": "api",
                    "providers": {"opencode-go": {"name": "OpenCode Go", "models": {
                        "glm-5": {"id": "glm-5", "name": "GLM 5", "cost": {"input": 0.0, "output": 0.0}},
                    }}},
                    "models": {},
                })

            handler._handle_get_model_suggestions()

            payload = captured["payload"]
            self.assertEqual(payload["source"], "modelsdev")
            self.assertEqual([m["id"] for m in payload["models"]], ["opencode-go/glm-5"])

    def test_registry_no_slug_returns_empty_not_all_models(self) -> None:
        """Gemini's bare tier ids cannot be mapped to a registry slug — the
        old fallback served ALL active models (cross-provider soup)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler, captured = self._make_suggestions_handler(root, provider="Gemini")

            handler._handle_get_model_suggestions()

            payload = captured["payload"]
            self.assertEqual(payload["source"], "registry")
            self.assertEqual(payload["models"], [])


# --------------------------------------------------------------------------- #
# models.dev import — overlay key id convention                               #
# --------------------------------------------------------------------------- #


class TestModelsDevImportOverlayKey(unittest.TestCase):
    """Imported models.dev prices must be persisted under the registry's id
    convention, otherwise _collect_models()'s overlay lookup silently misses
    and the imported price never surfaces in /api/models."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    def _import(self, root: Path, body: dict) -> dict:
        handler = _make_models_handler(root, _sample_registry_models())
        handler._read_body = mock.Mock(return_value=body)  # type: ignore[method-assign]
        captured: dict = {}
        handler._send_json = mock.Mock(  # type: ignore[method-assign]
            side_effect=lambda payload, status=200: captured.update({"payload": payload, "status": status}))
        handler._handle_post_models_dev_import()
        return captured["payload"]

    def _read_overlay(self, root: Path) -> dict:
        text = (root / "config" / "pricing-overlay.yaml").read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}

    def test_import_namespaced_provider_writes_prefixed_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = self._import(root, {
                "provider": "opencode-go", "model_id": "new-model",
                "input_cost": 1.5, "output_cost": 4.5,
            })
            self.assertTrue(payload["success"])
            prices = self._read_overlay(root)["prices"]["opencode-go"]
            self.assertIn("opencode-go/new-model", prices)
            self.assertNotIn("new-model", prices)
            self.assertEqual(prices["opencode-go/new-model"], {"input": 1.5, "output": 4.5})

    def test_import_bare_provider_writes_bare_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = self._import(root, {
                "provider": "anthropic", "model_id": "claude-new",
                "input_cost": 2.0, "output_cost": 8.0,
            })
            self.assertTrue(payload["success"])
            prices = self._read_overlay(root)["prices"]["anthropic"]
            self.assertIn("claude-new", prices)
            self.assertNotIn("anthropic/claude-new", prices)

    def test_first_ever_import_without_existing_overlay_file(self) -> None:
        """config/pricing-overlay.yaml does not exist yet — the import must
        create it instead of failing in the backup step (_backup reads the
        original file and would raise FileNotFoundError)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = _make_models_handler(root, _sample_registry_models())
            # No pricing-overlay.yaml written by the fixture — ensure that.
            self.assertFalse((root / "config" / "pricing-overlay.yaml").exists())
            handler._read_body = mock.Mock(return_value={  # type: ignore[method-assign]
                "provider": "opencode-go", "model_id": "brand-new",
                "input_cost": 0.0, "output_cost": 0.0,
            })
            captured: dict = {}
            handler._send_json = mock.Mock(  # type: ignore[method-assign]
                side_effect=lambda payload, status=200: captured.update({"payload": payload, "status": status}))

            handler._handle_post_models_dev_import()

            self.assertTrue(captured["payload"].get("success"), captured["payload"])
            prices = self._read_overlay(root)["prices"]["opencode-go"]
            self.assertIn("opencode-go/brand-new", prices)


# --------------------------------------------------------------------------- #
# Curation "disabled" — drift-tolerant id matching                            #
# --------------------------------------------------------------------------- #


class TestCollectModelsDisabledNormalization(unittest.TestCase):
    """Registry id formats drifted across discovery generations (bare vs.
    prefixed, dash vs. dot), so curation entries written against an older
    registry must still match via a normalized comparison."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    def _make_handler_with_curation(self, root: Path, disabled: list[str]) -> Any:
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "config" / "model-curation.yaml").write_text(
            yaml.dump({"disabled": disabled}, sort_keys=False), encoding="utf-8")
        registry = [
            # Current-generation id (prefixed, dot separator):
            {"id": "anthropic/claude-opus-4.1", "name": "Claude Opus 4.1", "provider": "anthropic",
             "input_cost_api": 15.0, "output_cost_api": 75.0},
            # Untouched model:
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic",
             "input_cost_api": 3.0, "output_cost_api": 15.0},
        ]
        return _make_models_handler(root, registry)

    def test_drifted_disabled_id_still_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler_with_curation(root, disabled=["claude-opus-4-1"])
            models = {m["id"]: m for m in handler._collect_models()}
            self.assertFalse(models["anthropic/claude-opus-4.1"]["enabled"])
            self.assertTrue(models["claude-sonnet-4-6"]["enabled"])

    def test_exact_disabled_id_keeps_working(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler_with_curation(
                root, disabled=["anthropic/claude-opus-4.1"])
            models = {m["id"]: m for m in handler._collect_models()}
            self.assertFalse(models["anthropic/claude-opus-4.1"]["enabled"])


# --------------------------------------------------------------------------- #
# models.dev loading — negative cache, error detail, force refresh            #
# --------------------------------------------------------------------------- #


class TestLoadModelsDevDataResilience(unittest.TestCase):
    """A total models.dev load failure must be negatively cached (so an
    unreachable network cannot re-attempt a 30 s fetch on every request),
    carry a human-readable reason, and ↻ (force_refresh) must prefer the
    live API over a stale SDK snapshot."""

    def setUp(self) -> None:
        _reset_models_dev_class_state()

    def tearDown(self) -> None:
        _reset_models_dev_class_state()
        admin_server.AdminRequestHandler.config_manager = None  # type: ignore[assignment]

    def _make_handler(self, root: Path) -> Any:
        return _make_models_handler(root, _sample_registry_models())

    def test_failure_is_negatively_cached_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root)
            # Patch at the urllib layer (NOT the loader methods) so the real
            # error-recording path inside _load_from_models_dev_api runs.
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
                first = handler._load_models_dev_data()
            self.assertEqual(first["source"], "error")
            self.assertIn("models.dev fetch failed", first["error"])
            self.assertIn("connection refused", first["error"])
            self.assertEqual(first["providers"], {})

            # Within the TTL the failure is re-served without re-fetching.
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")) as urlopen_mock:
                second = handler._load_models_dev_data()
            self.assertEqual(second, first)
            self.assertEqual(urlopen_mock.call_count, 0)

            # After the TTL expires the loader retries.
            error_ts = admin_server.AdminRequestHandler._models_dev_error[1]
            admin_server.AdminRequestHandler._models_dev_error = (first, error_ts - 3600)
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")) as urlopen_mock:
                handler._load_models_dev_data()
            self.assertEqual(urlopen_mock.call_count, 1)

    def test_stale_cache_served_before_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root)
            stale_payload = {"source": "api", "generated_at": "old", "providers": {"x": {}}, "models": {}}
            admin_server.AdminRequestHandler._models_dev_cache = stale_payload
            admin_server.AdminRequestHandler._models_dev_cache_ts = time.time() - 7200  # expired
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")) as urlopen_mock:
                result = handler._load_models_dev_data()
            self.assertEqual(result, stale_payload)
            self.assertEqual(urlopen_mock.call_count, 1)

            # Regression (M1): serving the stale cache must also STAMP the
            # negative cache — otherwise every subsequent request re-attempts
            # the 30 s fetch instead of re-serving the stale payload.
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")) as urlopen_mock:
                second = handler._load_models_dev_data()
            self.assertEqual(second, stale_payload)
            self.assertEqual(urlopen_mock.call_count, 0)

            # After the TTL expires the loader retries (and re-stamps).
            error_ts = admin_server.AdminRequestHandler._models_dev_error[1]
            admin_server.AdminRequestHandler._models_dev_error = (second, error_ts - 3600)
            with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")) as urlopen_mock:
                handler._load_models_dev_data()
            self.assertEqual(urlopen_mock.call_count, 1)

    @staticmethod
    def _urlopen_response(payload: dict) -> mock.MagicMock:
        """Build a urlopen() return value usable as a context manager whose
        ``read()`` yields the JSON ``payload``."""
        resp = mock.MagicMock()
        resp.read.return_value = json.dumps(payload).encode("utf-8")
        resp.__enter__.return_value = resp
        return resp

    def test_force_refresh_prefers_api_over_sdk_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root)
            resp = self._urlopen_response({"providers": {}, "models": {}})

            # force_refresh=True must hit the live API...
            with mock.patch("urllib.request.urlopen", return_value=resp):
                result = handler._load_models_dev_data(force_refresh=True)
            self.assertEqual(result["source"], "api")

            # ...while the normal load path keeps the documented SDK-primary
            # order (SDK snapshot first) once the caches are out of the way.
            _reset_models_dev_class_state()
            snapshot = root / "node_modules" / "@opencode-ai" / "models" / "dist"
            snapshot.mkdir(parents=True)
            # Content shaped like the real snapshot.js: a JS double-quoted
            # string with escaped quotes, parsed by _load_from_sdk_snapshot.
            (snapshot / "snapshot.js").write_text(
                'JSON.parse("{\\"providers\\":{\\"sdk-only\\":{}}}")\nexport const providers =',
                encoding="utf-8",
            )
            # The API must stay out of the picture here — offline behaviour
            # (and no accidental network access from unit tests).
            with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
                normal = handler._load_models_dev_data()
            self.assertEqual(normal["source"], "sdk")
            self.assertIn("sdk-only", normal["providers"])

    def test_successful_load_clears_negative_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handler = self._make_handler(root)
            error_payload = {"source": "error", "error": "down", "providers": {}, "models": {}}
            # Expired negative cache so the loader actually retries.
            admin_server.AdminRequestHandler._models_dev_error = (
                error_payload, time.time() - admin_server.AdminRequestHandler._MODELS_DEV_ERROR_TTL_SECONDS * 2)
            resp = self._urlopen_response({"providers": {}, "models": {}})

            with mock.patch("urllib.request.urlopen", return_value=resp):
                result = handler._load_models_dev_data()
            self.assertEqual(result["source"], "api")
            self.assertFalse(hasattr(admin_server.AdminRequestHandler, "_models_dev_error"))


if __name__ == "__main__":
    unittest.main()
