"""Unit tests for ``scripts/admin-server.py``.

The admin-server module is loaded via :mod:`importlib` because the file name
contains a hyphen (``admin-server.py``) which prevents the usual
``import scripts.admin_server`` syntax. The module is loaded once at module
import time and shared across test cases.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

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


if __name__ == "__main__":
    unittest.main()
